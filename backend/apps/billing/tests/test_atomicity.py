from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from apps.billing.models import Payment, Plan, Subscription, WebhookEvent
from apps.billing.services.subscriptions import (
    create_subscription_for_user,
    get_current_subscription,
)
from apps.billing.views import AsaasWebhookView

WEBHOOK_TOKEN = "billing-atomicity-token"


class AsaasWebhookAtomicityTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            email="atomicidade@teste.com",
            full_name="Teste Atomicidade",
        )
        self.plan = Plan.objects.create(
            name="Plano Atomicidade",
            slug="plano-atomicidade",
            price="89.90",
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status=Subscription.Status.PENDING,
            gateway_subscription_id="sub_atomicidade",
        )

    def post_webhook(self, payload):
        request = self.factory.post(
            "/api/v1/billing/webhooks/asaas/",
            payload,
            format="json",
            HTTP_X_WEBHOOK_TOKEN=WEBHOOK_TOKEN,
        )
        return AsaasWebhookView.as_view()(request)

    @override_settings(ASAAS_WEBHOOK_TOKEN=WEBHOOK_TOKEN, ASAAS_API_KEY="")
    def test_processing_failure_rolls_back_payment_and_subscription(self):
        payload = {
            "id": "evt_atomic_rollback",
            "event": "PAYMENT_CONFIRMED",
            "payment": {
                "id": "pay_atomic_rollback",
                "subscription": "sub_atomicidade",
                "value": 89.9,
                "confirmedDate": timezone.now().isoformat(),
            },
        }

        with patch(
            "apps.billing.integrations.webhooks.asaas.payments."
            "activate_subscription_from_payment",
            side_effect=RuntimeError("falha simulada"),
        ):
            response = self.post_webhook(payload)

        self.assertEqual(response.status_code, 200)
        self.subscription.refresh_from_db()
        event = WebhookEvent.objects.get(event_id="evt_atomic_rollback")
        self.assertEqual(self.subscription.status, Subscription.Status.PENDING)
        self.assertFalse(
            Payment.objects.filter(
                gateway_payment_id="pay_atomic_rollback"
            ).exists()
        )
        self.assertFalse(event.processed)
        self.assertIsNone(event.processed_at)
        self.assertEqual(
            event.error_message,
            "Falha interna ao processar o evento.",
        )

    @override_settings(ASAAS_WEBHOOK_TOKEN=WEBHOOK_TOKEN, ASAAS_API_KEY="")
    def test_confirmed_and_received_events_activate_same_payment_once(self):
        confirmed_at = timezone.now()
        first_response = self.post_webhook(
            {
                "id": "evt_atomic_confirmed",
                "event": "PAYMENT_CONFIRMED",
                "payment": {
                    "id": "pay_atomic_once",
                    "subscription": "sub_atomicidade",
                    "value": 89.9,
                    "confirmedDate": confirmed_at.isoformat(),
                },
            }
        )
        self.subscription.refresh_from_db()
        original_period_start = self.subscription.current_period_start
        original_period_end = self.subscription.current_period_end

        second_response = self.post_webhook(
            {
                "id": "evt_atomic_received",
                "event": "PAYMENT_RECEIVED",
                "payment": {
                    "id": "pay_atomic_once",
                    "subscription": "sub_atomicidade",
                    "value": 89.9,
                    "paymentDate": (
                        confirmed_at + timedelta(days=1)
                    ).isoformat(),
                },
            }
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.subscription.refresh_from_db()
        payment = Payment.objects.get(gateway_payment_id="pay_atomic_once")
        self.assertEqual(payment.status, Payment.Status.RECEIVED)
        self.assertEqual(
            self.subscription.current_period_start,
            original_period_start,
        )
        self.assertEqual(
            self.subscription.current_period_end,
            original_period_end,
        )
        self.assertEqual(
            self.subscription.metadata["last_activated_payment_id"],
            "pay_atomic_once",
        )

    @override_settings(ASAAS_WEBHOOK_TOKEN=WEBHOOK_TOKEN, ASAAS_API_KEY="")
    def test_out_of_order_created_event_does_not_downgrade_received_payment(self):
        self.post_webhook(
            {
                "id": "evt_atomic_received_first",
                "event": "PAYMENT_RECEIVED",
                "payment": {
                    "id": "pay_atomic_order",
                    "subscription": "sub_atomicidade",
                    "value": 89.9,
                    "paymentDate": timezone.now().isoformat(),
                },
            }
        )
        self.post_webhook(
            {
                "id": "evt_atomic_created_late",
                "event": "PAYMENT_CREATED",
                "payment": {
                    "id": "pay_atomic_order",
                    "subscription": "sub_atomicidade",
                    "value": 89.9,
                },
            }
        )

        payment = Payment.objects.get(gateway_payment_id="pay_atomic_order")
        self.assertEqual(payment.status, Payment.Status.RECEIVED)


class SubscriptionProvisioningAtomicityTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="provisionamento@teste.com",
            full_name="Teste Provisionamento",
        )
        self.plan = Plan.objects.create(
            name="Plano Provisionamento",
            slug="plano-provisionamento",
            price="99.90",
        )

    def test_gateway_calls_run_outside_database_transaction(self):
        class GatewayProbe:
            def create_customer(self, user, checkout_data):
                if connection.in_atomic_block:
                    raise AssertionError(
                        "create_customer executado dentro de transaction.atomic"
                    )
                return {"id": "cus_atomic"}

            def create_subscription(
                self,
                user,
                plan,
                checkout_data,
                customer_id,
            ):
                if connection.in_atomic_block:
                    raise AssertionError(
                        "create_subscription executado dentro de "
                        "transaction.atomic"
                    )
                return {"id": "sub_atomic", "status": "PENDING"}

            def cancel_subscription(self, subscription_id):
                return None

        with patch(
            "apps.billing.services.subscriptions.get_gateway",
            return_value=GatewayProbe(),
        ):
            subscription = create_subscription_for_user(self.user, self.plan)

        self.assertEqual(subscription.gateway_customer_id, "cus_atomic")
        self.assertEqual(subscription.gateway_subscription_id, "sub_atomic")
        self.assertEqual(
            subscription.metadata["provisioning_status"],
            "COMPLETED",
        )

    def test_gateway_failure_leaves_no_blocking_pending_subscription(self):
        class FailingGateway:
            def create_customer(self, user, checkout_data):
                return {"id": "cus_failure"}

            def create_subscription(
                self,
                user,
                plan,
                checkout_data,
                customer_id,
            ):
                raise RuntimeError("gateway indisponível")

            def cancel_subscription(self, subscription_id):
                return None

        with patch(
            "apps.billing.services.subscriptions.get_gateway",
            return_value=FailingGateway(),
        ):
            with self.assertRaises(RuntimeError):
                create_subscription_for_user(self.user, self.plan)

        subscription = Subscription.objects.get(user=self.user)
        self.assertEqual(subscription.status, Subscription.Status.CANCELED)
        self.assertEqual(
            subscription.metadata["provisioning_status"],
            "FAILED",
        )
        self.assertIsNone(get_current_subscription(self.user))
