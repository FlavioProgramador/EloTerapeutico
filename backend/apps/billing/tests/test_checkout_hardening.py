from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.billing.models import BillingOrder, Payment, Plan, PlanPrice, Subscription
from apps.billing.services.access import SubscriptionAccessService
from apps.billing.services.checkout import (
    CheckoutAlreadyPendingError,
    create_checkout_order,
)
from apps.billing.services.gateways.base import GatewayUnavailableError


class FakeCheckoutGateway:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.customer_calls = 0
        self.subscription_calls = 0

    def create_customer(self, user, checkout_data):
        self.customer_calls += 1
        return {"id": "cus_checkout_test"}

    def create_recurring_subscription(
        self,
        user,
        plan_price,
        checkout_data,
        *,
        customer_id=None,
    ):
        self.subscription_calls += 1
        if self.fail:
            raise GatewayUnavailableError()
        return {"id": "sub_checkout_test", "status": "PENDING"}

    def list_subscription_payments(self, gateway_subscription_id):
        return {"data": []}


class CheckoutHardeningTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="checkout.hardening@example.com",
            full_name="Checkout Hardening",
        )
        self.trial_plan = Plan.objects.create(
            name="Essencial",
            slug="checkout-trial-plan",
            price="49.90",
        )
        self.paid_plan = Plan.objects.create(
            name="Profissional",
            slug="checkout-paid-plan",
            price="99.90",
        )
        self.other_plan = Plan.objects.create(
            name="Clínica",
            slug="checkout-other-plan",
            price="199.90",
        )
        self.paid_price = PlanPrice.objects.create(
            plan=self.paid_plan,
            name="Profissional mensal",
            slug="checkout-paid-monthly",
            total_amount="99.90",
            billing_interval=PlanPrice.BillingInterval.MONTHLY,
            billing_model=PlanPrice.BillingModel.RECURRING,
        )
        self.other_price = PlanPrice.objects.create(
            plan=self.other_plan,
            name="Clínica mensal",
            slug="checkout-other-monthly",
            total_amount="199.90",
            billing_interval=PlanPrice.BillingInterval.MONTHLY,
            billing_model=PlanPrice.BillingModel.RECURRING,
        )
        now = timezone.now()
        self.trial = Subscription.objects.create(
            user=self.user,
            plan=self.trial_plan,
            status=Subscription.Status.TRIALING,
            started_at=now,
            access_starts_at=now,
            access_ends_at=now + timedelta(days=7),
            trial_ends_at=now + timedelta(days=7),
        )
        self.checkout_data = {
            "billingType": "PIX",
            "dueDate": timezone.localdate() + timedelta(days=1),
            "installmentCount": 1,
        }

    def test_trial_can_start_paid_checkout_without_losing_access(self):
        result = create_checkout_order(
            user=self.user,
            plan_price=self.paid_price,
            checkout_data=self.checkout_data,
            idempotency_key="trial-conversion-001",
            gateway=FakeCheckoutGateway(),
        )

        self.trial.refresh_from_db()
        self.assertTrue(result.created)
        self.assertEqual(result.order.status, BillingOrder.Status.PENDING)
        self.assertEqual(result.subscription.pk, self.trial.pk)
        self.assertEqual(self.trial.status, Subscription.Status.TRIALING)
        self.assertTrue(self.trial.has_access)
        self.assertTrue(result.order.metadata["conversion_from_trial"])

    def test_gateway_failure_does_not_cancel_trial(self):
        with self.assertRaises(GatewayUnavailableError):
            create_checkout_order(
                user=self.user,
                plan_price=self.paid_price,
                checkout_data=self.checkout_data,
                idempotency_key="trial-failure-001",
                gateway=FakeCheckoutGateway(fail=True),
            )

        self.trial.refresh_from_db()
        order = BillingOrder.objects.get(user=self.user)
        self.assertEqual(order.status, BillingOrder.Status.FAILED)
        self.assertEqual(self.trial.status, Subscription.Status.TRIALING)
        self.assertTrue(self.trial.has_access)
        self.assertEqual(self.trial.metadata["pending_checkout"]["status"], "FAILED")

    def test_same_idempotency_key_reuses_order_without_second_gateway_call(self):
        gateway = FakeCheckoutGateway()
        first = create_checkout_order(
            user=self.user,
            plan_price=self.paid_price,
            checkout_data=self.checkout_data,
            idempotency_key="same-key-001",
            gateway=gateway,
        )
        second = create_checkout_order(
            user=self.user,
            plan_price=self.paid_price,
            checkout_data=self.checkout_data,
            idempotency_key="same-key-001",
            gateway=gateway,
        )

        self.assertTrue(first.created)
        self.assertFalse(second.created)
        self.assertEqual(first.order.pk, second.order.pk)
        self.assertEqual(gateway.customer_calls, 1)
        self.assertEqual(gateway.subscription_calls, 1)
        self.assertEqual(BillingOrder.objects.count(), 1)

    def test_existing_pending_order_is_reused_with_new_key_for_same_price(self):
        gateway = FakeCheckoutGateway()
        first = create_checkout_order(
            user=self.user,
            plan_price=self.paid_price,
            checkout_data=self.checkout_data,
            idempotency_key="pending-key-001",
            gateway=gateway,
        )
        second = create_checkout_order(
            user=self.user,
            plan_price=self.paid_price,
            checkout_data=self.checkout_data,
            idempotency_key="pending-key-002",
            gateway=gateway,
        )

        self.assertFalse(second.created)
        self.assertEqual(first.order.pk, second.order.pk)
        self.assertEqual(gateway.subscription_calls, 1)

    def test_pending_order_for_another_price_blocks_duplicate_intention(self):
        first = create_checkout_order(
            user=self.user,
            plan_price=self.paid_price,
            checkout_data=self.checkout_data,
            idempotency_key="pending-plan-001",
            gateway=FakeCheckoutGateway(),
        )

        with self.assertRaises(CheckoutAlreadyPendingError) as context:
            create_checkout_order(
                user=self.user,
                plan_price=self.other_price,
                checkout_data=self.checkout_data,
                idempotency_key="pending-plan-002",
                gateway=FakeCheckoutGateway(),
            )

        self.assertEqual(
            context.exception.details["order_public_id"],
            str(first.order.public_id),
        )
        self.assertEqual(BillingOrder.objects.count(), 1)

    def test_new_key_after_failed_order_can_retry(self):
        with self.assertRaises(GatewayUnavailableError):
            create_checkout_order(
                user=self.user,
                plan_price=self.paid_price,
                checkout_data=self.checkout_data,
                idempotency_key="failed-attempt-001",
                gateway=FakeCheckoutGateway(fail=True),
            )

        retried = create_checkout_order(
            user=self.user,
            plan_price=self.paid_price,
            checkout_data=self.checkout_data,
            idempotency_key="failed-attempt-002",
            gateway=FakeCheckoutGateway(),
        )

        self.assertTrue(retried.created)
        self.assertEqual(retried.order.status, BillingOrder.Status.PENDING)
        self.assertEqual(BillingOrder.objects.filter(status=BillingOrder.Status.FAILED).count(), 1)
        self.assertEqual(BillingOrder.objects.filter(status=BillingOrder.Status.PENDING).count(), 1)

    def test_confirmed_payment_converts_trial_to_paid_subscription(self):
        result = create_checkout_order(
            user=self.user,
            plan_price=self.paid_price,
            checkout_data=self.checkout_data,
            idempotency_key="trial-confirmed-001",
            gateway=FakeCheckoutGateway(),
        )
        payment = Payment.objects.create(
            billing_order=result.order,
            subscription=self.trial,
            user=self.user,
            amount=self.paid_price.total_amount,
            status=Payment.Status.CONFIRMED,
            paid_at=timezone.now(),
            gateway_payment_id="pay_trial_confirmed",
            gateway_subscription_id="sub_checkout_test",
        )

        activated = SubscriptionAccessService.activate_from_payment(self.trial, payment)

        self.assertEqual(activated.status, Subscription.Status.ACTIVE)
        self.assertEqual(activated.plan, self.paid_plan)
        self.assertEqual(activated.billing_order, result.order)
        self.assertEqual(activated.gateway_subscription_id, "sub_checkout_test")
