from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.billing.models import BillingOrder, Payment, Plan, PlanPrice


@pytest.fixture
def user(db):
    user_model = get_user_model()
    return user_model.objects.create_user(
        email="perf.billing@example.com",
        password="password123",
        full_name="Perf Billing User",
    )


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.mark.django_db
def test_billing_order_list_optimized_queries(api_client, user, django_assert_num_queries):
    """Garante número constante de consultas (3 consultas) ao listar pedidos paginados pré-carregados com pagamentos."""

    plan = Plan.objects.create(
        name="Profissional Test",
        slug="profissional-perf-test",
        price="99.90",
    )
    plan_price = PlanPrice.objects.create(
        plan=plan,
        name="Profissional Anual",
        slug="profissional-anual-perf-test",
        total_amount="999.00",
        billing_interval=PlanPrice.BillingInterval.YEARLY,
        billing_model=PlanPrice.BillingModel.INSTALLMENT,
    )

    num_orders = 5
    for i in range(num_orders):
        order = BillingOrder.objects.create(
            user=user,
            plan=plan,
            plan_price=plan_price,
            total_amount=999.00,
            installment_count=12,
            idempotency_key=f"order-key-{i}",
            external_reference=f"ext-ref-{i}",
        )
        today = timezone.localdate()
        Payment.objects.create(
            user=user,
            billing_order=order,
            amount=83.25,
            status=Payment.Status.CONFIRMED,
            due_date=today - timedelta(days=30),
        )
        Payment.objects.create(
            user=user,
            billing_order=order,
            amount=83.25,
            status=Payment.Status.PENDING,
            due_date=today + timedelta(days=30),
        )

    # 1 consulta para contagem de paginação DRF (COUNT)
    # 1 consulta para obter os BillingOrders com select_related("plan", "plan_price", "plan_price__plan")
    # 1 consulta para o prefetch_related("payments")
    with django_assert_num_queries(3):
        response = api_client.get("/api/v1/billing/orders/")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == num_orders
    for item in response.data["results"]:
        assert item["paid_installments"] == 1
        assert item["next_due_date"] is not None
