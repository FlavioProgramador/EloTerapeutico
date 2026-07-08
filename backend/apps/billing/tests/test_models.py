from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.billing.models import Payment, Plan, Subscription, WebhookEvent


class BillingModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="terapeuta@example.com",
            full_name="Terapeuta Teste",
        )
        self.plan = Plan.objects.create(
            name="Profissional",
            slug="profissional-test",
            price="89.90",
            has_financial=True,
            has_reports=True,
        )

    def test_create_plan(self):
        self.assertEqual(str(self.plan), "Profissional")
        self.assertTrue(self.plan.has_agenda)
        self.assertEqual(self.plan.currency, "BRL")

    def test_create_subscription(self):
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status=Subscription.Status.PENDING,
            gateway_subscription_id="sub_123",
        )
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.status, Subscription.Status.PENDING)

    def test_gateway_payment_id_is_unique(self):
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            gateway_subscription_id="sub_123",
        )
        Payment.objects.create(
            subscription=subscription,
            user=self.user,
            amount="89.90",
            gateway_payment_id="pay_123",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Payment.objects.create(
                subscription=subscription,
                user=self.user,
                amount="89.90",
                gateway_payment_id="pay_123",
            )

    def test_webhook_payload_hash_is_unique(self):
        WebhookEvent.objects.create(
            gateway_name="ASAAS",
            event_type="PAYMENT_CONFIRMED",
            payload_hash="abc",
            payload={"event": "PAYMENT_CONFIRMED"},
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            WebhookEvent.objects.create(
                gateway_name="ASAAS",
                event_type="PAYMENT_CONFIRMED",
                payload_hash="abc",
                payload={"event": "PAYMENT_CONFIRMED"},
            )
