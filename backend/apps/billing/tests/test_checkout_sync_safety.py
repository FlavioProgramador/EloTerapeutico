from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.billing.models import BillingOrder, Plan, PlanPrice, Subscription
from apps.billing.services.checkout import create_checkout_order
from apps.billing.services.gateways.base import GatewayUnavailableError


class GatewayWithDeferredSync:
    def __init__(self):
        self.subscription_calls = 0

    def create_customer(self, user, checkout_data):
        return {"id": "cus_deferred_sync"}

    def create_recurring_subscription(
        self,
        user,
        plan_price,
        checkout_data,
        *,
        customer_id=None,
    ):
        self.subscription_calls += 1
        return {"id": "sub_deferred_sync", "status": "PENDING"}

    def list_subscription_payments(self, gateway_subscription_id):
        raise GatewayUnavailableError()


class CheckoutSyncSafetyTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="checkout.sync@example.com",
            full_name="Checkout Sync",
        )
        self.plan = Plan.objects.create(
            name="Profissional",
            slug="checkout-sync-plan",
            price="99.90",
        )
        self.price = PlanPrice.objects.create(
            plan=self.plan,
            name="Mensal",
            slug="checkout-sync-monthly",
            total_amount="99.90",
            billing_interval=PlanPrice.BillingInterval.MONTHLY,
            billing_model=PlanPrice.BillingModel.RECURRING,
        )
        self.checkout_data = {
            "billingType": "PIX",
            "dueDate": timezone.localdate() + timedelta(days=1),
            "installmentCount": 1,
        }

    def test_external_creation_followed_by_sync_failure_stays_pending(self):
        gateway = GatewayWithDeferredSync()

        first = create_checkout_order(
            user=self.user,
            plan_price=self.price,
            checkout_data=self.checkout_data,
            idempotency_key="deferred-sync-001",
            gateway=gateway,
        )
        replay = create_checkout_order(
            user=self.user,
            plan_price=self.price,
            checkout_data=self.checkout_data,
            idempotency_key="deferred-sync-002",
            gateway=gateway,
        )

        first.order.refresh_from_db()
        self.assertEqual(first.order.status, BillingOrder.Status.PENDING)
        self.assertEqual(first.order.gateway_subscription_id, "sub_deferred_sync")
        self.assertEqual(first.order.metadata["initial_sync_status"], "RETRY_REQUIRED")
        self.assertFalse(replay.created)
        self.assertEqual(replay.order.pk, first.order.pk)
        self.assertEqual(gateway.subscription_calls, 1)
        self.assertEqual(Subscription.objects.get(user=self.user).status, Subscription.Status.PENDING)
