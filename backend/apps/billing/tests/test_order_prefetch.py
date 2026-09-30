import pytest
from datetime import date
from django.contrib.auth import get_user_model
from apps.billing.models import BillingOrder, Payment, Plan, PlanPrice
from apps.billing.api.v1.serializers import BillingOrderSerializer
from apps.billing.selectors.orders import get_orders_for_user

User = get_user_model()


@pytest.mark.django_db
def test_billing_order_serializer_uses_prefetched_payments(django_assert_num_queries):
    user = User.objects.create_user(
        email="test_prefetch@example.test",
        password="Password123!",
        full_name="User Prefetch",
    )
    plan = Plan.objects.create(
        name="Plano Teste",
        slug="plano-teste",
        price="100.00",
        max_patients=10,
        max_storage_mb=500,
    )
    plan_price = PlanPrice.objects.create(
        plan=plan,
        name="Mensal",
        slug="mensal",
        total_amount="100.00",
        billing_interval="MONTHLY",
    )

    # Create 3 orders with 2 payments each
    orders = []
    for i in range(3):
        order = BillingOrder.objects.create(
            user=user,
            plan=plan,
            plan_price=plan_price,
            total_amount="100.00",
            idempotency_key=f"order_idem_{i}",
            external_reference=f"ext_ref_{i}",
        )
        Payment.objects.create(
            user=user,
            billing_order=order,
            amount="50.00",
            status=Payment.Status.CONFIRMED,
            due_date=date(2025, 1, 1),
            gateway_payment_id=f"pay_conf_{i}",
        )
        Payment.objects.create(
            user=user,
            billing_order=order,
            amount="50.00",
            status=Payment.Status.PENDING,
            due_date=date(2025, 2, 1),
            gateway_payment_id=f"pay_pend_{i}",
        )
        orders.append(order)

    # Fetch orders using selector (which prefetches payments and select_related plan_price__plan)
    qs = list(get_orders_for_user(user=user))

    # Serializing all 3 orders should perform 0 additional DB queries
    with django_assert_num_queries(0):
        serialized_data = BillingOrderSerializer(qs, many=True).data

    assert len(serialized_data) == 3
    for item in serialized_data:
        assert item["paid_installments"] == 1
        assert item["next_due_date"] == date(2025, 2, 1)
