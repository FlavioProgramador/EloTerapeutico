from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from apps.billing.models import Payment, Plan, Subscription, WebhookEvent
from apps.billing.security import REDACTED_VALUE
from apps.billing.views import AsaasWebhookView

WEBHOOK_HEADER_VALUE = "billing-webhook-fixture"


class AsaasWebhookTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            email="terapeuta@example.com",
            full_name="Terapeuta Teste",
        )
        self.plan = Plan.objects.create(
            name="Profissional",
            slug="profissional-test",
            price="89.90",
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            status=Subscription.Status.PENDING,
            gateway_subscription_id="sub_123",
        )

    def post_webhook(self, payload, *, token=WEBHOOK_HEADER_VALUE):
        request = self.factory.post(
            "/api/v1/billing/webhooks/asaas/",
            payload,
            format="json",
            HTTP_X_WEBHOOK_TOKEN=token,
        )
        return AsaasWebhookView.as_view()(request)

    @override_settings(ASAAS_WEBHOOK_TOKEN=WEBHOOK_HEADER_VALUE, ASAAS_API_KEY="")
    def test_payment_confirmed_activates_subscription(self):
        response = self.post_webhook(
            {
                "event": "PAYMENT_CONFIRMED",
                "payment": {
                    "id": "pay_123",
                    "subscription": "sub_123",
                    "value": 89.9,
                    "dueDate": "2026-07-08",
                    "confirmedDate": timezone.now().isoformat(),
                },
            }
        )

        self.assertEqual(response.status_code, 200)
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, Subscription.Status.ACTIVE)
        self.assertTrue(
            Payment.objects.filter(
                gateway_payment_id="pay_123",
                status=Payment.Status.CONFIRMED,
            ).exists()
        )

    @override_settings(ASAAS_WEBHOOK_TOKEN=WEBHOOK_HEADER_VALUE, ASAAS_API_KEY="")
    def test_payment_received_activates_subscription(self):
        response = self.post_webhook(
            {
                "event": "PAYMENT_RECEIVED",
                "payment": {
                    "id": "pay_124",
                    "subscription": "sub_123",
                    "value": 89.9,
                    "dueDate": "2026-07-08",
                    "paymentDate": timezone.now().isoformat(),
                },
            }
        )

        self.assertEqual(response.status_code, 200)
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, Subscription.Status.ACTIVE)

    @override_settings(ASAAS_WEBHOOK_TOKEN=WEBHOOK_HEADER_VALUE, ASAAS_API_KEY="")
    def test_payment_overdue_marks_subscription_past_due(self):
        self.subscription.status = Subscription.Status.ACTIVE
        self.subscription.save(update_fields=["status"])
        response = self.post_webhook(
            {
                "event": "PAYMENT_OVERDUE",
                "payment": {
                    "id": "pay_125",
                    "subscription": "sub_123",
                    "value": 89.9,
                    "dueDate": "2026-07-08",
                },
            }
        )

        self.assertEqual(response.status_code, 200)
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, Subscription.Status.PAST_DUE)

    @override_settings(ASAAS_WEBHOOK_TOKEN=WEBHOOK_HEADER_VALUE, ASAAS_API_KEY="")
    def test_duplicate_event_is_idempotent(self):
        payload = {
            "event": "PAYMENT_CONFIRMED",
            "payment": {
                "id": "pay_126",
                "subscription": "sub_123",
                "value": 89.9,
                "dueDate": "2026-07-08",
                "confirmedDate": timezone.now().isoformat(),
            },
        }
        self.post_webhook(payload)
        self.post_webhook(payload)

        self.assertEqual(WebhookEvent.objects.count(), 1)
        self.assertEqual(Payment.objects.filter(gateway_payment_id="pay_126").count(), 1)

    @override_settings(ASAAS_WEBHOOK_TOKEN=WEBHOOK_HEADER_VALUE, ASAAS_API_KEY="")
    def test_event_without_subscription_does_not_break(self):
        response = self.post_webhook(
            {
                "event": "PAYMENT_CONFIRMED",
                "payment": {
                    "id": "pay_127",
                    "value": 89.9,
                    "dueDate": "2026-07-08",
                },
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WebhookEvent.objects.count(), 1)
        self.assertIn("sem subscription", WebhookEvent.objects.first().error_message)

    @override_settings(ASAAS_WEBHOOK_TOKEN=WEBHOOK_HEADER_VALUE, ASAAS_API_KEY="")
    def test_invalid_webhook_token_is_rejected_without_persistence(self):
        response = self.post_webhook(
            {"event": "PAYMENT_CREATED", "payment": {"id": "pay_invalid"}},
            token="invalid-token",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["detail"], "Webhook inválido.")
        self.assertFalse(WebhookEvent.objects.exists())
        self.assertFalse(Payment.objects.filter(gateway_payment_id="pay_invalid").exists())

    @override_settings(ASAAS_WEBHOOK_TOKEN=WEBHOOK_HEADER_VALUE, ASAAS_API_KEY="")
    def test_sensitive_webhook_fields_are_redacted_in_raw_payloads(self):
        response = self.post_webhook(
            {
                "id": "evt_sensitive_123",
                "event": "PAYMENT_CONFIRMED",
                "access_token": "must-not-be-stored",
                "payment": {
                    "id": "pay_sensitive_123",
                    "subscription": "sub_123",
                    "value": 89.9,
                    "dueDate": "2026-07-08",
                    "confirmedDate": timezone.now().isoformat(),
                    "cpfCnpj": "52998224725",
                    "creditCardToken": "card-token",
                    "pixQrCode": "private-qr-code",
                    "pixCopyPaste": "private-pix-copy-paste",
                },
            }
        )

        self.assertEqual(response.status_code, 200)
        event = WebhookEvent.objects.get(event_id="evt_sensitive_123")
        payment = Payment.objects.get(gateway_payment_id="pay_sensitive_123")

        self.assertEqual(event.payload["access_token"], REDACTED_VALUE)
        self.assertEqual(event.payload["payment"]["cpfCnpj"], REDACTED_VALUE)
        self.assertEqual(event.payload["payment"]["creditCardToken"], REDACTED_VALUE)
        self.assertEqual(event.payload["payment"]["pixQrCode"], REDACTED_VALUE)
        self.assertEqual(payment.raw_payload["cpfCnpj"], REDACTED_VALUE)
        self.assertEqual(payment.raw_payload["creditCardToken"], REDACTED_VALUE)
        self.assertEqual(payment.raw_payload["pixCopyPaste"], REDACTED_VALUE)

        # Os campos funcionais continuam disponíveis no registro protegido do pagamento.
        self.assertEqual(payment.pix_qr_code, "private-qr-code")
        self.assertEqual(payment.pix_copy_paste, "private-pix-copy-paste")
