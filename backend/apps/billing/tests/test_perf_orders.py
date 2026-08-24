from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from apps.billing.api.v1.serializers import BillingOrderSerializer
from apps.billing.models import BillingOrder, Payment, Plan, PlanPrice
from apps.billing.selectors.orders import get_orders_for_user


class BillingOrderPerfTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            email="perf_user@example.com",
            full_name="Perf User",
        )
        self.plan = Plan.objects.create(
            name="Plano Perf",
            slug="plano-perf",
            price="100.00",
        )
        self.price = PlanPrice.objects.create(
            plan=self.plan,
            name="Preço Perf",
            slug="preco-perf",
            total_amount="100.00",
            billing_interval=PlanPrice.BillingInterval.MONTHLY,
            billing_model=PlanPrice.BillingModel.RECURRING,
        )

        for i in range(5):
            order = BillingOrder.objects.create(
                user=self.user,
                plan=self.plan,
                plan_price=self.price,
                total_amount=Decimal("100.00"),
                idempotency_key=f"key-perf-{i}",
                external_reference=f"ext-perf-{i}",
            )
            Payment.objects.create(
                user=self.user,
                billing_order=order,
                amount=Decimal("100.00"),
                status=Payment.Status.PENDING,
                due_date=date(2025, 1, 1),
            )

    def test_billing_orders_listing_queries_are_constant(self):
        with CaptureQueriesContext(connection) as ctx:
            orders = list(get_orders_for_user(user=self.user))
            data = BillingOrderSerializer(orders, many=True).data

        self.assertEqual(len(data), 5)
        # Should be 2 queries total (1 for BillingOrder with select_related, 1 prefetch for Payments)
        self.assertLessEqual(len(ctx.captured_queries), 2)
