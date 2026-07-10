"""Testes adicionais de idempotência do webhook Asaas."""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory

from apps.billing.models import Payment, Plan, Subscription, WebhookEvent
from apps.billing.views import AsaasWebhookView

WEBHOOK_TOKEN = "billing-idempotency-token"


class AsaasWebhookEventIdTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            email="idempotency@teste.com",
            full_name="Idempotency Test",
        )
        self.plan = Plan.objects.create(
            name="Plano Idempotência",
            slug="plano-idempotencia",
            price="89.90",
        )
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            gateway_subscription_id="sub_idempotency",
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
    def test_same_event_id_with_different_payload_is_not_created_twice(self):
        base_payload = {
            "id": "evt_idempotency_123",
            "event": "PAYMENT_CONFIRMED",
            "payment": {
                "id": "pay_idempotency_123",
                "subscription": "sub_idempotency",
                "value": 89.9,
                "dueDate": "2026-07-10",
            },
        }
        first_response = self.post_webhook(base_payload)
        second_response = self.post_webhook(
            {
                **base_payload,
                "deliveryAttempt": 2,
                "payment": {
                    **base_payload["payment"],
                    "observations": "Payload reenviado pelo provedor",
                },
            }
        )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(WebhookEvent.objects.filter(event_id="evt_idempotency_123").count(), 1)
        self.assertEqual(Payment.objects.filter(gateway_payment_id="pay_idempotency_123").count(), 1)
