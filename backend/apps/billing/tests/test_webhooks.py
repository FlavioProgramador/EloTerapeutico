from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from apps.billing.models import BillingOrder, Payment, Plan, PlanPrice, Subscription, WebhookEvent
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
            slug="profissional-webhook-test",
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
    def test_payment_confirmed_activates_legacy_subscription_and_creates_order(self):
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
        self.assertIsNotNone(self.subscription.billing_order_id)
        self.assertTrue(
            Payment.objects.filter(
                gateway_payment_id="pay_123",
                status=Payment.Status.CONFIRMED,
            ).exists()
        )
        self.assertEqual(WebhookEvent.objects.get().status, WebhookEvent.Status.PROCESSED)

    @override_settings(ASAAS_WEBHOOK_TOKEN=WEBHOOK_HEADER_VALUE, ASAAS_API_KEY="")
    def test_payment_received_reactivates_past_due_subscription(self):
        self.subscription.status = Subscription.Status.PAST_DUE
        self.subscription.grace_period_ends_at = timezone.now()
        self.subscription.save(update_fields=["status", "grace_period_ends_at"])

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
        self.assertIsNone(self.subscription.grace_period_ends_at)

    @override_settings(
        ASAAS_WEBHOOK_TOKEN=WEBHOOK_HEADER_VALUE,
        ASAAS_API_KEY="",
        BILLING_GRACE_PERIOD_DAYS=5,
    )
    def test_payment_overdue_marks_subscription_past_due_with_grace_period(self):
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
        self.assertIsNotNone(self.subscription.grace_period_ends_at)

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
        self.assertEqual(WebhookEvent.objects.get().attempt_count, 1)

    @override_settings(
        ASAAS_WEBHOOK_TOKEN=WEBHOOK_HEADER_VALUE,
        ASAAS_API_KEY="",
        BILLING_WEBHOOK_MAX_RETRIES=3,
    )
    def test_event_received_before_order_is_kept_for_retry(self):
        response = self.post_webhook(
            {
                "event": "PAYMENT_CONFIRMED",
                "payment": {
                    "id": "pay_127",
                    "installment": "installment-not-created-yet",
                    "externalReference": "order-not-created-yet",
                    "value": 89.9,
                    "dueDate": "2026-07-08",
                },
            }
        )

        self.assertEqual(response.status_code, 200)
        event = WebhookEvent.objects.get()
        self.assertEqual(event.status, WebhookEvent.Status.RETRY)
        self.assertFalse(event.processed)
        self.assertIsNotNone(event.next_retry_at)
        self.assertIn("não localizada", event.last_error)

    @override_settings(ASAAS_WEBHOOK_TOKEN=WEBHOOK_HEADER_VALUE, ASAAS_API_KEY="")
    def test_installment_event_is_resolved_by_external_reference(self):
        price = PlanPrice.objects.create(
            plan=self.plan,
            name="Anual parcelado",
            slug="annual-installment-webhook-test",
            total_amount="999.00",
            billing_interval=PlanPrice.BillingInterval.YEARLY,
            billing_model=PlanPrice.BillingModel.INSTALLMENT,
            installments_enabled=True,
            min_installments=2,
            max_installments=12,
        )
        order = BillingOrder.objects.create(
            user=self.user,
            plan=self.plan,
            plan_price=price,
            status=BillingOrder.Status.PENDING,
            billing_model=price.billing_model,
            billing_interval=price.billing_interval,
            currency="BRL",
            total_amount="999.00",
            installment_count=12,
            installment_amount_estimate="83.25",
            external_reference="elo-order-webhook-installment",
            idempotency_key="webhook-installment-idempotency",
        )
        self.subscription.billing_order = order
        self.subscription.gateway_subscription_id = ""
        self.subscription.save(update_fields=["billing_order", "gateway_subscription_id"])

        response = self.post_webhook(
            {
                "event": "PAYMENT_CONFIRMED",
                "payment": {
                    "id": "pay_installment_5",
                    "installment": "ins_123",
                    "installmentNumber": 5,
                    "externalReference": order.external_reference,
                    "value": 83.25,
                    "dueDate": "2026-11-08",
                    "confirmedDate": timezone.now().isoformat(),
                },
            }
        )

        self.assertEqual(response.status_code, 200)
        payment = Payment.objects.get(gateway_payment_id="pay_installment_5")
        self.assertEqual(payment.billing_order, order)
        self.assertEqual(payment.installment_number, 5)
        self.assertEqual(payment.installment_count, 12)
        self.assertEqual(payment.amount, Decimal("83.25"))

    @override_settings(ASAAS_WEBHOOK_TOKEN=WEBHOOK_HEADER_VALUE, ASAAS_API_KEY="")
    def test_chargeback_suspends_access(self):
        self.subscription.status = Subscription.Status.ACTIVE
        self.subscription.save(update_fields=["status"])
        response = self.post_webhook(
            {
                "event": "PAYMENT_CHARGEBACK_REQUESTED",
                "payment": {
                    "id": "pay_chargeback",
                    "subscription": "sub_123",
                    "value": 89.9,
                    "dueDate": "2026-07-08",
                },
            }
        )

        self.assertEqual(response.status_code, 200)
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, Subscription.Status.SUSPENDED)
        self.assertIsNotNone(self.subscription.suspended_at)

    @override_settings(ASAAS_WEBHOOK_TOKEN=WEBHOOK_HEADER_VALUE, ASAAS_API_KEY="")
    def test_invalid_webhook_token_is_rejected_without_persistence(self):
        response = self.post_webhook(
            {"event": "PAYMENT_CREATED", "payment": {"id": "pay_invalid"}},
            token="invalid-token",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["detail"], "Webhook inválido.")
        self.assertFalse(WebhookEvent.objects.exists())

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
        self.assertEqual(payment.raw_payload["cpfCnpj"], REDACTED_VALUE)
        self.assertEqual(payment.raw_payload["creditCardToken"], REDACTED_VALUE)
        self.assertEqual(payment.pix_qr_code, "private-qr-code")
        self.assertEqual(payment.pix_copy_paste, "private-pix-copy-paste")
