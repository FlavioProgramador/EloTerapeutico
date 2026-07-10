from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.billing.models import BillingOrder, Payment, Plan, PlanPrice, Subscription
from apps.billing.services.access import SubscriptionAccessService
from apps.billing.services.orders import create_billing_order


class SubscriptionAccessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="access@example.com",
            full_name="Teste Acesso",
        )
        self.plan = Plan.objects.create(
            name="Profissional",
            slug="professional-access-test",
            price="99.90",
        )
        self.monthly = PlanPrice.objects.create(
            plan=self.plan,
            name="Mensal",
            slug="monthly-access-test",
            total_amount="99.90",
            billing_interval=PlanPrice.BillingInterval.MONTHLY,
            billing_model=PlanPrice.BillingModel.RECURRING,
        )
        self.annual = PlanPrice.objects.create(
            plan=self.plan,
            name="Anual",
            slug="annual-access-test",
            total_amount="999.00",
            billing_interval=PlanPrice.BillingInterval.YEARLY,
            billing_model=PlanPrice.BillingModel.ONE_TIME,
        )

    def create_order_and_subscription(self, price, paid_at):
        order = BillingOrder.objects.create(
            user=self.user,
            plan=self.plan,
            plan_price=price,
            status=BillingOrder.Status.PENDING,
            billing_model=price.billing_model,
            billing_interval=price.billing_interval,
            currency="BRL",
            total_amount=price.total_amount,
            installment_count=1,
            installment_amount_estimate=price.total_amount,
            external_reference=f"access-order-{price.pk}",
            idempotency_key=f"access-idempotency-{price.pk}",
        )
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            billing_order=order,
            status=Subscription.Status.PENDING,
        )
        payment = Payment.objects.create(
            billing_order=order,
            subscription=subscription,
            user=self.user,
            amount=price.total_amount,
            status=Payment.Status.CONFIRMED,
            paid_at=paid_at,
            gateway_payment_id=f"pay-access-{price.pk}",
        )
        return order, subscription, payment

    def test_monthly_period_uses_calendar_month_instead_of_thirty_days(self):
        paid_at = timezone.make_aware(datetime(2026, 1, 31, 10, 0))
        _, subscription, payment = self.create_order_and_subscription(self.monthly, paid_at)

        activated = SubscriptionAccessService.activate_from_payment(subscription, payment)

        self.assertEqual(activated.access_starts_at, paid_at)
        self.assertEqual(activated.access_ends_at, paid_at + relativedelta(months=1))
        self.assertEqual(activated.access_ends_at.day, 28)

    def test_annual_period_handles_leap_year(self):
        paid_at = timezone.make_aware(datetime(2024, 2, 29, 10, 0))
        _, subscription, payment = self.create_order_and_subscription(self.annual, paid_at)

        activated = SubscriptionAccessService.activate_from_payment(subscription, payment)

        self.assertEqual(activated.access_ends_at, paid_at + relativedelta(years=1))
        self.assertEqual(activated.access_ends_at.date().isoformat(), "2025-02-28")

    @override_settings(BILLING_GRACE_PERIOD_DAYS=5)
    def test_grace_period_expires_and_suspends_subscription(self):
        _, subscription, payment = self.create_order_and_subscription(self.monthly, timezone.now())
        activated = SubscriptionAccessService.activate_from_payment(subscription, payment)
        past_due = SubscriptionAccessService.mark_past_due(activated)
        past_due.grace_period_ends_at = timezone.now() - timedelta(minutes=1)
        past_due.save(update_fields=["grace_period_ends_at"])

        suspended = SubscriptionAccessService.suspend_if_grace_expired(past_due)

        self.assertEqual(suspended.status, Subscription.Status.SUSPENDED)
        self.assertIsNotNone(suspended.suspended_at)

    def test_cancel_at_period_end_preserves_current_access(self):
        _, subscription, payment = self.create_order_and_subscription(self.monthly, timezone.now())
        activated = SubscriptionAccessService.activate_from_payment(subscription, payment)

        scheduled = SubscriptionAccessService.schedule_cancellation(activated)

        self.assertTrue(scheduled.cancel_at_period_end)
        self.assertEqual(scheduled.status, Subscription.Status.ACTIVE)
        self.assertTrue(scheduled.has_access)


class PlanChangeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="change@example.com",
            full_name="Teste Troca",
        )
        self.basic = Plan.objects.create(name="Básico", slug="basic-change-test", price="49.90")
        self.professional = Plan.objects.create(name="Profissional", slug="professional-change-test", price="99.90")
        self.basic_price = PlanPrice.objects.create(
            plan=self.basic,
            name="Básico mensal",
            slug="basic-monthly-change-test",
            total_amount="49.90",
            billing_interval=PlanPrice.BillingInterval.MONTHLY,
            billing_model=PlanPrice.BillingModel.RECURRING,
        )
        self.professional_price = PlanPrice.objects.create(
            plan=self.professional,
            name="Profissional mensal",
            slug="professional-monthly-change-test",
            total_amount="99.90",
            billing_interval=PlanPrice.BillingInterval.MONTHLY,
            billing_model=PlanPrice.BillingModel.RECURRING,
        )
        old_order = BillingOrder.objects.create(
            user=self.user,
            plan=self.basic,
            plan_price=self.basic_price,
            status=BillingOrder.Status.PAID,
            billing_model=self.basic_price.billing_model,
            billing_interval=self.basic_price.billing_interval,
            currency="BRL",
            total_amount="49.90",
            installment_count=1,
            installment_amount_estimate="49.90",
            gateway_customer_id="cus_change",
            gateway_subscription_id="sub_old",
            external_reference="old-change-order",
            idempotency_key="old-change-idempotency",
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan=self.basic,
            billing_order=old_order,
            status=Subscription.Status.ACTIVE,
            started_at=timezone.now() - timedelta(days=10),
            access_starts_at=timezone.now() - timedelta(days=10),
            access_ends_at=timezone.now() + timedelta(days=20),
            current_period_start=timezone.now() - timedelta(days=10),
            current_period_end=timezone.now() + timedelta(days=20),
            gateway_customer_id="cus_change",
            gateway_subscription_id="sub_old",
        )

    @patch("apps.billing.services.orders.get_gateway")
    def test_new_checkout_does_not_replace_active_plan_before_confirmation(self, get_gateway_mock):
        gateway = Mock()
        gateway.create_recurring_subscription.return_value = {"id": "sub_new", "status": "PENDING"}
        gateway.list_subscription_payments.return_value = {"data": []}
        get_gateway_mock.return_value = gateway

        order, subscription = create_billing_order(
            user=self.user,
            plan_price=self.professional_price,
            checkout_data={
                "billingType": "PIX",
                "dueDate": timezone.localdate() + timedelta(days=1),
                "installmentCount": 1,
            },
            idempotency_key="safe-plan-change-001",
        )

        subscription.refresh_from_db()
        self.assertEqual(subscription.plan, self.basic)
        self.assertEqual(subscription.gateway_subscription_id, "sub_old")
        self.assertEqual(subscription.status, Subscription.Status.ACTIVE)
        self.assertTrue(order.metadata["is_plan_change"])
        self.assertEqual(order.gateway_subscription_id, "sub_new")

    @patch("apps.billing.services.orders.get_gateway")
    def test_confirmed_new_payment_effectively_changes_plan(self, get_gateway_mock):
        gateway = Mock()
        gateway.create_recurring_subscription.return_value = {"id": "sub_new", "status": "PENDING"}
        gateway.list_subscription_payments.return_value = {"data": []}
        get_gateway_mock.return_value = gateway
        order, subscription = create_billing_order(
            user=self.user,
            plan_price=self.professional_price,
            checkout_data={
                "billingType": "PIX",
                "dueDate": timezone.localdate() + timedelta(days=1),
                "installmentCount": 1,
            },
            idempotency_key="confirmed-plan-change-001",
        )
        payment = Payment.objects.create(
            billing_order=order,
            subscription=subscription,
            user=self.user,
            amount="99.90",
            status=Payment.Status.CONFIRMED,
            paid_at=timezone.now(),
            gateway_payment_id="pay_new_plan",
            gateway_subscription_id="sub_new",
        )

        activated = SubscriptionAccessService.activate_from_payment(subscription, payment)

        self.assertEqual(activated.plan, self.professional)
        self.assertEqual(activated.billing_order, order)
        self.assertEqual(activated.gateway_subscription_id, "sub_new")
        order.refresh_from_db()
        self.assertTrue(order.metadata["previous_subscription_cancel_pending"])
        self.assertEqual(order.metadata["previous_gateway_subscription_id"], "sub_old")
