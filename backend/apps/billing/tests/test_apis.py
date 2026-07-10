from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Payment, Plan, Subscription


class BillingAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            email="terapeuta@example.com",
            full_name="Terapeuta Teste",
        )
        self.other_user = user_model.objects.create_user(
            email="outro@example.com",
            full_name="Outro Terapeuta",
        )
        self.plan = Plan.objects.create(
            name="Profissional",
            slug="profissional-test",
            price="89.90",
            has_financial=True,
        )

    def test_list_active_plans(self):
        response = self.client.get("/api/v1/billing/plans/")

        self.assertEqual(response.status_code, 200)
        slugs = {plan["slug"] for plan in response.data["results"]}
        self.assertIn("profissional-test", slugs)

    @override_settings(BILLING_TRIAL_DAYS=0)
    @patch("apps.billing.services.subscriptions.get_gateway")
    def test_create_subscription(self, get_gateway_mock):
        gateway = Mock()
        gateway.create_customer.return_value = {"id": "cus_123"}
        gateway.create_subscription.return_value = {"id": "sub_123", "status": "PENDING"}
        get_gateway_mock.return_value = gateway
        self.client.force_authenticate(self.user)

        response = self.client.post(
            "/api/v1/billing/subscription/create/",
            {"plan_id": self.plan.id},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["gateway_status"], "PENDING")
        self.assertEqual(response.data["status"], Subscription.Status.PENDING)
        self.assertTrue(
            Subscription.objects.filter(
                user=self.user,
                gateway_subscription_id="sub_123",
                status=Subscription.Status.PENDING,
            ).exists()
        )

    def test_checkout_preview_uses_plan_price_and_asaas_naming(self):
        self.client.force_authenticate(self.user)
        due_date = (timezone.localdate() + timedelta(days=2)).isoformat()

        response = self.client.post(
            "/api/v1/billing/checkout/preview/",
            {
                "plan_slug": self.plan.slug,
                "type": "SUBSCRIPTION",
                "billingType": "PIX",
                "cpfCnpj": "529.982.247-25",
                "dueDate": due_date,
                "value": "1.00",
                "description": "Plano Profissional",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["gateway"], "ASAAS")
        self.assertEqual(response.data["checkout"]["billingType"], "PIX")
        self.assertEqual(response.data["checkout"]["dueDate"], due_date)
        self.assertEqual(response.data["checkout"]["value"], "89.90")
        self.assertIn("webhook", response.data["activation_rule"].lower())

    @patch("apps.billing.services.subscriptions.get_gateway")
    def test_checkout_create_subscription_keeps_status_pending_until_webhook(self, get_gateway_mock):
        gateway = Mock()
        gateway.create_customer.return_value = {"id": "cus_checkout"}
        gateway.create_subscription.return_value = {"id": "sub_checkout", "status": "PENDING"}
        get_gateway_mock.return_value = gateway
        self.client.force_authenticate(self.user)
        due_date = (timezone.localdate() + timedelta(days=1)).isoformat()

        response = self.client.post(
            "/api/v1/billing/checkout/create/",
            {
                "plan_slug": self.plan.slug,
                "type": "SUBSCRIPTION",
                "billingType": "BOLETO",
                "cpfCnpj": "529.982.247-25",
                "dueDate": due_date,
                "description": "Assinatura Profissional",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["subscription"]["status"], Subscription.Status.PENDING)
        self.assertEqual(gateway.create_customer.call_args.args[1]["cpfCnpj"], "52998224725")
        gateway.create_subscription.assert_called_once()
        subscription = Subscription.objects.get(gateway_subscription_id="sub_checkout")
        self.assertEqual(subscription.status, Subscription.Status.PENDING)
        self.assertEqual(subscription.metadata["checkout"]["billingType"], "BOLETO")
        self.assertNotIn("cpfCnpj", subscription.metadata["checkout"])

    @override_settings(ASAAS_API_KEY="test-api-key")
    @patch("apps.billing.views.AsaasGateway")
    def test_one_time_checkout_does_not_expose_raw_gateway_payload(self, gateway_class_mock):
        gateway_class_mock.return_value.create_payment.return_value = {
            "id": "pay_public_123",
            "status": "PENDING",
            "invoiceUrl": "https://example.com/invoice/123",
            "bankSlipUrl": "https://example.com/boleto/123",
            "customer": "cus_private_123",
            "cpfCnpj": "52998224725",
            "creditCardToken": "token-that-must-not-leak",
            "apiKey": "secret-that-must-not-leak",
        }
        self.client.force_authenticate(self.user)
        due_date = (timezone.localdate() + timedelta(days=1)).isoformat()

        response = self.client.post(
            "/api/v1/billing/checkout/create/",
            {
                "plan_slug": self.plan.slug,
                "type": "ONE_TIME",
                "billingType": "PIX",
                "cpfCnpj": "529.982.247-25",
                "dueDate": due_date,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["payment"],
            {
                "gateway_payment_id": "pay_public_123",
                "status": "PENDING",
                "invoiceUrl": "https://example.com/invoice/123",
                "bankSlipUrl": "https://example.com/boleto/123",
            },
        )
        self.assertNotIn("raw_gateway_response", response.data["payment"])
        self.assertNotIn("customer", response.data["payment"])
        self.assertNotIn("cpfCnpj", response.data["payment"])
        self.assertNotIn("creditCardToken", response.data["payment"])

    def test_checkout_rejects_invalid_cpf_cnpj(self):
        self.client.force_authenticate(self.user)
        due_date = (timezone.localdate() + timedelta(days=1)).isoformat()

        response = self.client.post(
            "/api/v1/billing/checkout/preview/",
            {
                "plan_slug": self.plan.slug,
                "type": "SUBSCRIPTION",
                "billingType": "BOLETO",
                "cpfCnpj": "111.111.111-11",
                "dueDate": due_date,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("cpfCnpj", response.data["error"]["details"])

    def test_checkout_rejects_credit_card_without_tokenization(self):
        self.client.force_authenticate(self.user)
        due_date = (timezone.localdate() + timedelta(days=1)).isoformat()

        response = self.client.post(
            "/api/v1/billing/checkout/create/",
            {
                "plan_slug": self.plan.slug,
                "type": "SUBSCRIPTION",
                "billingType": "CREDIT_CARD",
                "cpfCnpj": "529.982.247-25",
                "dueDate": due_date,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("tokenização", str(response.data))

    def test_payments_list_only_current_user_payments(self):
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            gateway_subscription_id="sub_123",
        )
        other_subscription = Subscription.objects.create(
            user=self.other_user,
            plan=self.plan,
            gateway_subscription_id="sub_999",
        )
        Payment.objects.create(
            subscription=subscription,
            user=self.user,
            amount="89.90",
            gateway_payment_id="pay_123",
        )
        Payment.objects.create(
            subscription=other_subscription,
            user=self.other_user,
            amount="89.90",
            gateway_payment_id="pay_999",
        )
        self.client.force_authenticate(self.user)

        response = self.client.get("/api/v1/billing/payments/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["id"],
            Payment.objects.get(gateway_payment_id="pay_123").id,
        )
