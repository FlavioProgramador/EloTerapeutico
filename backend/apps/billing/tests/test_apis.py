from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.billing.models import Payment, Plan, Subscription


class BillingAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        User = get_user_model()
        self.user = User.objects.create_user(
            email="terapeuta@example.com",
            full_name="Terapeuta Teste",
            password="SenhaForte123",
        )
        self.other_user = User.objects.create_user(
            email="outro@example.com",
            full_name="Outro Terapeuta",
            password="SenhaForte123",
        )
        self.plan = Plan.objects.create(name="Profissional", slug="profissional-test", price="89.90", has_financial=True)

    def test_list_active_plans(self):
        response = self.client.get("/api/v1/billing/plans/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["slug"], "profissional-test")

    @override_settings(BILLING_TRIAL_DAYS=0)
    @patch("apps.billing.services.subscriptions.get_gateway")
    def test_create_subscription(self, get_gateway_mock):
        gateway = Mock()
        gateway.create_customer.return_value = {"id": "cus_123"}
        gateway.create_subscription.return_value = {"id": "sub_123", "status": "ACTIVE"}
        get_gateway_mock.return_value = gateway
        self.client.force_authenticate(self.user)

        response = self.client.post("/api/v1/billing/subscription/create/", {"plan_id": self.plan.id}, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["gateway_status"], "ACTIVE")
        self.assertTrue(Subscription.objects.filter(user=self.user, gateway_subscription_id="sub_123").exists())

    def test_payments_list_only_current_user_payments(self):
        subscription = Subscription.objects.create(user=self.user, plan=self.plan, gateway_subscription_id="sub_123")
        other_subscription = Subscription.objects.create(
            user=self.other_user,
            plan=self.plan,
            gateway_subscription_id="sub_999",
        )
        Payment.objects.create(subscription=subscription, user=self.user, amount="89.90", gateway_payment_id="pay_123")
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
        self.assertEqual(response.data["results"][0]["id"], Payment.objects.get(gateway_payment_id="pay_123").id)
