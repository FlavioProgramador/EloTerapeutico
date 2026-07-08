from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.billing.models import Payment, Plan, Subscription
from apps.billing.services.subscriptions import (
    activate_subscription_from_payment,
    create_subscription_for_user,
    mark_subscription_past_due,
)


class SubscriptionServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="terapeuta@example.com",
            full_name="Terapeuta Teste",
            password="SenhaForte123",
        )
        self.plan = Plan.objects.create(name="Profissional", slug="profissional-test", price="89.90", has_financial=True)

    @override_settings(BILLING_TRIAL_DAYS=7)
    @patch("apps.billing.services.subscriptions.get_gateway")
    def test_create_subscription_for_active_plan(self, get_gateway_mock):
        gateway = Mock()
        gateway.create_customer.return_value = {"id": "cus_123"}
        gateway.create_subscription.return_value = {"id": "sub_123", "status": "ACTIVE"}
        get_gateway_mock.return_value = gateway

        subscription = create_subscription_for_user(self.user, self.plan)

        self.assertEqual(subscription.status, Subscription.Status.TRIALING)
        self.assertEqual(subscription.gateway_customer_id, "cus_123")
        self.assertEqual(subscription.gateway_subscription_id, "sub_123")

    @override_settings(BILLING_TRIAL_DAYS=0)
    @patch("apps.billing.services.subscriptions.get_gateway")
    def test_prevent_duplicate_subscription(self, get_gateway_mock):
        gateway = Mock()
        gateway.create_customer.return_value = {"id": "cus_123"}
        gateway.create_subscription.return_value = {"id": "sub_123", "status": "ACTIVE"}
        get_gateway_mock.return_value = gateway
        create_subscription_for_user(self.user, self.plan)

        with self.assertRaises(ValidationError):
            create_subscription_for_user(self.user, self.plan)

    def test_inactive_plan_raises_error(self):
        self.plan.is_active = False
        self.plan.save(update_fields=["is_active"])
        with self.assertRaises(ValidationError):
            create_subscription_for_user(self.user, self.plan)

    def test_activate_subscription_from_payment(self):
        subscription = Subscription.objects.create(user=self.user, plan=self.plan, status=Subscription.Status.PENDING)
        payment = Payment.objects.create(
            subscription=subscription,
            user=self.user,
            amount="89.90",
            status=Payment.Status.PENDING,
            paid_at=timezone.now(),
        )

        activate_subscription_from_payment(subscription, payment)

        subscription.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(subscription.status, Subscription.Status.ACTIVE)
        self.assertEqual(payment.status, Payment.Status.CONFIRMED)

    def test_mark_subscription_past_due(self):
        subscription = Subscription.objects.create(user=self.user, plan=self.plan, status=Subscription.Status.ACTIVE)
        mark_subscription_past_due(subscription)
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, Subscription.Status.PAST_DUE)
