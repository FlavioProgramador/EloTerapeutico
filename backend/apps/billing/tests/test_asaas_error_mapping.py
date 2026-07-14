from datetime import timedelta
from unittest.mock import MagicMock, patch

import httpx
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import BillingOrder, Plan, PlanPrice, Subscription
from apps.billing.services.gateways.base import (
    GatewayAuthenticationError,
    GatewayConfigurationError,
    GatewayUnavailableError,
    GatewayValidationError,
)
from infrastructure.payments.asaas.client import AsaasGateway


class AsaasErrorMappingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="asaas.errors@example.com",
            full_name="Asaas Errors",
        )

    @override_settings(ASAAS_API_KEY="")
    def test_missing_api_key_raises_configuration_error(self):
        with self.assertRaises(GatewayConfigurationError):
            AsaasGateway()

    @override_settings(ASAAS_API_KEY="")
    def test_health_check_reports_not_configured_without_exposing_secret(self):
        health = AsaasGateway(require_api_key=False).health_check()

        self.assertFalse(health["connected"])
        self.assertFalse(health["configured"])
        self.assertEqual(health["environment"], "SANDBOX")
        self.assertNotIn("api_key", health)

    @override_settings(ASAAS_BASE_URL="https://gateway-invalido.example/v3")
    def test_unknown_base_url_is_rejected(self):
        with self.assertRaises(GatewayConfigurationError):
            AsaasGateway()

    @patch.object(AsaasGateway, "_request")
    def test_customer_payload_is_normalized(self, request_mock):
        request_mock.return_value = {"id": "cus_normalized"}
        gateway = AsaasGateway()

        gateway.create_customer(
            self.user,
            {
                "name": " Pessoa Teste ",
                "email": "PESSOA@EXAMPLE.COM",
                "cpfCnpj": "123.456.789-09",
                "phone": "(21) 99999-9999",
            },
        )

        payload = request_mock.call_args.kwargs["json"]
        self.assertEqual(payload["name"], "Pessoa Teste")
        self.assertEqual(payload["email"], "pessoa@example.com")
        self.assertEqual(payload["cpfCnpj"], "12345678909")
        self.assertEqual(payload["mobilePhone"], "21999999999")

    def test_invalid_phone_is_rejected_before_gateway_call(self):
        gateway = AsaasGateway()

        with self.assertRaises(GatewayValidationError) as context:
            gateway.create_customer(
                self.user,
                {
                    "name": "Pessoa Teste",
                    "email": "pessoa@example.com",
                    "phone": "123",
                },
            )

        self.assertIn("phone", context.exception.details)

    @patch("infrastructure.payments.asaas.client.httpx.Client")
    def test_gateway_401_is_mapped_to_authentication_error(self, client_class):
        request = httpx.Request("GET", "https://api-sandbox.asaas.com/v3/customers")
        response = httpx.Response(
            401,
            request=request,
            json={"errors": [{"description": "access_token inválido"}]},
        )
        client = MagicMock()
        client.request.return_value = response
        client_class.return_value.__enter__.return_value = client

        with self.assertRaises(GatewayAuthenticationError):
            AsaasGateway().health_check()

    @patch("infrastructure.payments.asaas.client.httpx.Client")
    def test_timeout_is_mapped_to_service_unavailable(self, client_class):
        client = MagicMock()
        client.request.side_effect = httpx.ConnectTimeout("timeout")
        client_class.return_value.__enter__.return_value = client

        with self.assertRaises(GatewayUnavailableError):
            AsaasGateway().health_check()

    @override_settings(DEBUG=False, ASAAS_WEBHOOK_TOKEN="")
    def test_webhook_without_configured_token_is_rejected_in_production(self):
        request = MagicMock()
        request.headers = {}

        with self.assertRaises(PermissionDenied):
            AsaasGateway(require_api_key=False).parse_webhook(request)


class CheckoutErrorResponseTests(TestCase):
    endpoint = "/api/v1/billing/checkout/create/"

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="checkout.response@example.com",
            full_name="Checkout Response",
        )
        self.plan = Plan.objects.create(
            name="Profissional",
            slug="checkout-response-plan",
            price="99.90",
        )
        self.price = PlanPrice.objects.create(
            plan=self.plan,
            name="Mensal",
            slug="checkout-response-monthly",
            total_amount="99.90",
            billing_interval=PlanPrice.BillingInterval.MONTHLY,
            billing_model=PlanPrice.BillingModel.RECURRING,
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.payload = {
            "plan_price_id": self.price.pk,
            "billingType": "PIX",
            "cpfCnpj": "529.982.247-25",
            "name": "Checkout Response",
            "email": "checkout.response@example.com",
            "phone": "(21) 99999-9999",
            "dueDate": (timezone.localdate() + timedelta(days=1)).isoformat(),
            "installmentCount": 1,
            "idempotency_key": "checkout-response-001",
        }

    @override_settings(ASAAS_API_KEY="")
    def test_missing_gateway_configuration_returns_503_with_stable_code(self):
        response = self.client.post(
            self.endpoint,
            self.payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="checkout-response-001",
        )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["error"]["code"], "ASAAS_CONFIGURATION_ERROR")
        self.assertEqual(
            response.data["error"]["message"],
            "A integração de pagamentos não está configurada.",
        )
        self.assertEqual(BillingOrder.objects.get(user=self.user).status, BillingOrder.Status.FAILED)
        self.assertEqual(
            Subscription.objects.get(user=self.user).status,
            Subscription.Status.CANCELED,
        )

    def test_invalid_document_returns_400_with_field_details(self):
        self.payload["cpfCnpj"] = "123"

        response = self.client.post(
            self.endpoint,
            self.payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="checkout-response-001",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "CHECKOUT_VALIDATION_ERROR")
        self.assertIn("cpfCnpj", response.data["error"]["details"])
        self.assertFalse(BillingOrder.objects.exists())
