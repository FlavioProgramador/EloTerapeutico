import pytest
from datetime import date
from decimal import Decimal
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient
from apps.financeiro.models import FinancialTransaction
from apps.users.models import User

@pytest.fixture
def perf_context(db):
    user = User.objects.create_user(
        email="perf-financeiro@example.com",
        full_name="Profissional Performance",
        password="safe-test-password",
        role=User.Role.THERAPIST,
    )
    client = APIClient()
    client.force_authenticate(user)

    # Create some data to make the summary interesting
    common = {"therapist": user, "due_date": date(2026, 7, 10)}
    # 1. Paid Income
    FinancialTransaction.objects.create(
        **common,
        transaction_type="income",
        amount=Decimal("1000.00"),
        paid_amount=Decimal("1000.00"),
        payment_status="paid",
        paid_at="2026-07-05T12:00:00Z",
    )
    # 2. Pending Income
    FinancialTransaction.objects.create(
        **common,
        transaction_type="income",
        amount=Decimal("500.00"),
        payment_status="pending",
    )
    # 3. Pending Expense
    FinancialTransaction.objects.create(
        **common,
        transaction_type="expense",
        amount=Decimal("200.00"),
        payment_status="pending",
    )
    # 4. Paid Expense
    FinancialTransaction.objects.create(
        **common,
        transaction_type="expense",
        amount=Decimal("300.00"),
        paid_amount=Decimal("300.00"),
        payment_status="paid",
        paid_at="2026-07-06T12:00:00Z",
    )

    return client, user

@pytest.mark.django_db
def test_summary_performance_query_count(perf_context):
    client, user = perf_context
    url = "/api/v1/financeiro/summary/"

    params = {"start_date": "2026-07-01", "end_date": "2026-07-31"}

    with CaptureQueriesContext(connection) as queries:
        response = client.get(url, params)

    assert response.status_code == 200
    print(f"\nNumber of queries: {len(queries)}")
    for i, q in enumerate(queries):
        print(f"Query {i+1}: {q['sql'][:100]}...")

    # After optimization, should be 1 main query (+ auth query if any, but CaptureQueriesContext in test might only see the main ones)
    assert len(queries) <= 2

    # Verify values are still correct
    data = response.data
    assert Decimal(data["received"]) == Decimal("1000.00")
    assert Decimal(data["paid_expenses"]) == Decimal("300.00")
    assert Decimal(data["receivable"]) == Decimal("500.00")
    assert Decimal(data["payable"]) == Decimal("200.00")
    assert data["received_count"] == 1
    assert data["paid_expenses_count"] == 1
    assert data["receivable_count"] == 1
    assert data["payable_count"] == 1
    assert data["transaction_count"] == 4
