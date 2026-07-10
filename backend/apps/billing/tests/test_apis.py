from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import BillingOrder, Payment, Plan, PlanPrice, Subscription


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
            price="99.90",
            has_financial=True,
        )
        self.monthly = PlanPrice.objects.create(
            plan=self.plan,
            name="Profissional Mensal",
            slug="profissional-mensal-test",
            total_amount="99.90",
            billing_interval=PlanPrice.BillingInterval.MONTHLY,
            billing_model=PlanPrice.BillingModel.RECURRING,
        )
        self.annual = PlanPrice.objects.create(
            plan=self.plan,
            name="Profissional Anual Parcelado",
            slug="profissional-anual-parcelado-test",
            total_amount="999.00",
            billing_interval=PlanPrice.BillingInterval.YEARLY,
            billing_model=PlanPrice.BillingModel.INSTALLMENT,
            discount_percentage="16.67",
            installments_enabled=True,
            min_installments=2,
            max_installments=12,
        )

    def authenticate(self):
        self.client.force_authenticate(self.user)

    @staticmethod
    def due_date(days=1):
        return (timezone.localdate() + timedelta(days=days)).isoformat()

    def test_list_active_plans_includes_commercial_prices(self):
        response = self.client.get("/api/v1/billing/plans/")

        self.assertEqual(response.status_code, 200)
        plan = next(item for item in response.data["results"] if item["slug"] == self.plan.slug)
        self.assertEqual(len(plan["prices"]), 2)
        self.assertEqual({price["billing_model"] for price in plan["prices"]}, {"RECURRING", "INSTALLMENT"})

    def test_preview_uses_registered_price_and_ignores_browser_value(self):
        self.authenticate()
        response = self.client.post(
            "/api/v1/billing/checkout/preview/",
            {
                "plan_price_id": self.annual.pk,
                "billingType": "PIX",
                "cpfCnpj": "529.982.247-25",
                "dueDate": self.due_date(2),
                "installmentCount": 12,
                "value": "1.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["checkout"]["totalAmount"], "999.00")
        self.assertEqual(response.data["checkout"]["installmentCount"], 12)
        self.assertEqual(response.data["checkout"]["installmentAmountEstimate"], "83.25")
        self.assertIn("frontend", response.data["activation_rule"].lower())

    @patch("apps.billing.services.orders.get_gateway")
    def test_monthly_checkout_stays_pending_until_webhook(self, get_gateway_mock):
        gateway = Mock()
        gateway.create_customer.return_value = {"id": "cus_monthly"}
        gateway.create_recurring_subscription.return_value = {"id": "sub_monthly", "status": "PENDING"}
        gateway.list_subscription_payments.return_value = {"data": []}
        get_gateway_mock.return_value = gateway
        self.authenticate()

        response = self.client.post(
            "/api/v1/billing/checkout/create/",
            {
                "plan_price_id": self.monthly.pk,
                "billingType": "BOLETO",
                "cpfCnpj": "529.982.247-25",
                "dueDate": self.due_date(),
                "installmentCount": 1,
                "idempotency_key": "monthly-checkout-test-001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["subscription"]["status"], Subscription.Status.PENDING)
        self.assertEqual(response.data["order"]["billing_model"], PlanPrice.BillingModel.RECURRING)
        self.assertEqual(gateway.create_customer.call_args.args[1]["cpfCnpj"], "52998224725")
        gateway.create_recurring_subscription.assert_called_once()
        self.assertTrue(BillingOrder.objects.filter(gateway_subscription_id="sub_monthly").exists())

    @patch("apps.billing.services.orders.get_gateway")
    def test_annual_installment_creates_all_twelve_invoices(self, get_gateway_mock):
        gateway = Mock()
        gateway.create_customer.return_value = {"id": "cus_annual"}
        gateway.create_installment_payment.return_value = {
            "id": "pay_installment_1",
            "installment": "ins_annual_12",
            "installmentNumber": 1,
            "value": 83.25,
            "status": "PENDING",
            "billingType": "BOLETO",
            "dueDate": self.due_date(),
            "invoiceUrl": "https://example.test/invoice/1",
        }
        gateway.list_installment_payments.return_value = {
            "data": [
                {
                    "id": f"pay_installment_{number}",
                    "installment": "ins_annual_12",
                    "installmentNumber": number,
                    "value": 83.25,
                    "status": "PENDING",
                    "billingType": "BOLETO",
                    "dueDate": (timezone.localdate() + timedelta(days=30 * number)).isoformat(),
                    "invoiceUrl": f"https://example.test/invoice/{number}",
                    "externalReference": "external-ref",
                }
                for number in range(1, 13)
            ]
        }
        get_gateway_mock.return_value = gateway
        self.authenticate()

        response = self.client.post(
            "/api/v1/billing/checkout/create/",
            {
                "plan_price_id": self.annual.pk,
                "billingType": "BOLETO",
                "cpfCnpj": "529.982.247-25",
                "dueDate": self.due_date(),
                "installmentCount": 12,
                "idempotency_key": "annual-checkout-test-001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data["payments"]), 12)
        self.assertEqual(response.data["payments"][0]["installment_label"], "Parcela 1 de 12")
        order = BillingOrder.objects.get(gateway_installment_id="ins_annual_12")
        self.assertEqual(order.installment_count, 12)
        self.assertEqual(order.payments.count(), 12)
        self.assertEqual(
            order.payments.aggregate_total if hasattr(order.payments, "aggregate_total") else sum(
                (payment.amount for payment in order.payments.all()), Decimal("0.00")
            ),
            Decimal("999.00"),
        )
        sent_payload = gateway.create_installment_payment.call_args.args[1]
        self.assertEqual(sent_payload["totalValue"], Decimal("999.00"))
        self.assertEqual(sent_payload["installmentCount"], 12)

    @patch("apps.billing.services.orders.get_gateway")
    def test_same_idempotency_key_does_not_duplicate_order_or_gateway_charge(self, get_gateway_mock):
        gateway = Mock()
        gateway.create_customer.return_value = {"id": "cus_idempotent"}
        gateway.create_recurring_subscription.return_value = {"id": "sub_idempotent", "status": "PENDING"}
        gateway.list_subscription_payments.return_value = {"data": []}
        get_gateway_mock.return_value = gateway
        self.authenticate()
        payload = {
            "plan_price_id": self.monthly.pk,
            "billingType": "PIX",
            "cpfCnpj": "529.982.247-25",
            "dueDate": self.due_date(),
            "installmentCount": 1,
            "idempotency_key": "same-key-for-retry-001",
        }

        first = self.client.post("/api/v1/billing/checkout/create/", payload, format="json")
        second = self.client.post("/api/v1/billing/checkout/create/", payload, format="json")

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(BillingOrder.objects.filter(user=self.user).count(), 1)
        gateway.create_recurring_subscription.assert_called_once()
        self.assertEqual(first.data["order"]["public_id"], second.data["order"]["public_id"])

    @patch("apps.billing.services.orders.get_gateway")
    def test_public_checkout_response_never_exposes_gateway_secrets(self, get_gateway_mock):
        gateway = Mock()
        gateway.create_customer.return_value = {"id": "cus_private"}
        gateway.create_single_payment.return_value = {
            "id": "pay_public_123",
            "status": "PENDING",
            "value": 999,
            "billingType": "PIX",
            "dueDate": self.due_date(),
            "invoiceUrl": "https://example.test/invoice/123",
            "customer": "cus_private",
            "cpfCnpj": "52998224725",
            "creditCardToken": "must-not-leak",
            "apiKey": "must-not-leak",
        }
        get_gateway_mock.return_value = gateway
        annual_cash = PlanPrice.objects.create(
            plan=self.plan,
            name="Profissional Anual à vista",
            slug="profissional-anual-vista-test",
            total_amount="999.00",
            billing_interval=PlanPrice.BillingInterval.YEARLY,
            billing_model=PlanPrice.BillingModel.ONE_TIME,
        )
        self.authenticate()

        response = self.client.post(
            "/api/v1/billing/checkout/create/",
            {
                "plan_price_id": annual_cash.pk,
                "billingType": "PIX",
                "cpfCnpj": "529.982.247-25",
                "dueDate": self.due_date(),
                "installmentCount": 1,
                "idempotency_key": "cash-checkout-test-001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        serialized = str(response.data)
        self.assertNotIn("must-not-leak", serialized)
        self.assertNotIn("cus_private", serialized)
        self.assertEqual(response.data["payments"][0]["invoice_url"], "https://example.test/invoice/123")

    def test_checkout_rejects_invalid_cpf_cnpj(self):
        self.authenticate()
        response = self.client.post(
            "/api/v1/billing/checkout/preview/",
            {
                "plan_price_id": self.monthly.pk,
                "billingType": "BOLETO",
                "cpfCnpj": "111.111.111-11",
                "dueDate": self.due_date(),
                "installmentCount": 1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("cpfCnpj", str(response.data))

    def test_checkout_rejects_credit_card_without_tokenization(self):
        self.authenticate()
        response = self.client.post(
            "/api/v1/billing/checkout/create/",
            {
                "plan_price_id": self.monthly.pk,
                "billingType": "CREDIT_CARD",
                "cpfCnpj": "529.982.247-25",
                "dueDate": self.due_date(),
                "installmentCount": 1,
                "idempotency_key": "credit-card-test-001",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("tokenização", str(response.data))

    def test_payments_are_isolated_by_user(self):
        subscription = Subscription.objects.create(user=self.user, plan=self.plan, gateway_subscription_id="sub_123")
        other_subscription = Subscription.objects.create(user=self.other_user, plan=self.plan, gateway_subscription_id="sub_999")
        own = Payment.objects.create(subscription=subscription, user=self.user, amount="89.90", gateway_payment_id="pay_123")
        Payment.objects.create(subscription=other_subscription, user=self.other_user, amount="89.90", gateway_payment_id="pay_999")
        self.authenticate()

        response = self.client.get("/api/v1/billing/payments/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], own.id)
