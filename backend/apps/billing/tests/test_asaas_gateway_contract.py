from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.billing.models import Plan, PlanPrice
from infrastructure.payments.asaas.client import AsaasGateway


@override_settings(
    ASAAS_API_KEY="test-api-key",
    ASAAS_BASE_URL="https://api-sandbox.asaas.com/v3",
)
class AsaasGatewayContractTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="gateway.contract@example.com",
            full_name="Contrato Gateway",
        )
        self.plan = Plan.objects.create(
            name="Profissional",
            slug="gateway-contract-plan",
            price="99.90",
        )
        self.price = PlanPrice.objects.create(
            plan=self.plan,
            name="Profissional anual parcelado",
            slug="gateway-contract-annual",
            total_amount="999.00",
            billing_interval=PlanPrice.BillingInterval.YEARLY,
            billing_model=PlanPrice.BillingModel.INSTALLMENT,
            installments_enabled=True,
            min_installments=2,
            max_installments=12,
        )
        self.gateway = AsaasGateway()

    @patch.object(AsaasGateway, "_request")
    def test_installment_uses_total_value_instead_of_manual_installment_value(self, request_mock):
        request_mock.return_value = {"id": "pay_1", "installment": "ins_1"}

        self.gateway.create_installment_payment(
            self.user,
            {
                "billingType": "BOLETO",
                "dueDate": timezone.localdate() + timedelta(days=1),
                "totalValue": Decimal("999.00"),
                "installmentCount": 12,
                "externalReference": "elo-order-contract-test",
            },
            customer_id="cus_contract",
        )

        _, path = request_mock.call_args.args
        payload = request_mock.call_args.kwargs["json"]
        self.assertEqual(path, "/payments")
        self.assertEqual(payload["installmentCount"], 12)
        self.assertEqual(payload["totalValue"], 999.0)
        self.assertNotIn("installmentValue", payload)
        self.assertNotIn("value", payload)

    @patch.object(AsaasGateway, "_request")
    def test_lists_all_payments_from_installment_endpoint(self, request_mock):
        request_mock.return_value = {"data": []}

        response = self.gateway.list_installment_payments("ins_123")

        request_mock.assert_called_once_with("GET", "/installments/ins_123/payments")
        self.assertEqual(response, {"data": []})

    @patch.object(AsaasGateway, "_request")
    def test_lists_recurring_subscription_payments(self, request_mock):
        request_mock.return_value = {"data": []}

        response = self.gateway.list_subscription_payments("sub_123")

        request_mock.assert_called_once_with("GET", "/subscriptions/sub_123/payments")
        self.assertEqual(response, {"data": []})
