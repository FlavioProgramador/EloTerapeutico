from datetime import date
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.finances.models import FinancialTransaction
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
    common = {"therapist": user, "due_date": date(2026, 7, 10)}
    FinancialTransaction.objects.create(**common, transaction_type="income", amount=Decimal("1000.00"), paid_amount=Decimal("1000.00"), payment_status="paid", paid_at="2026-07-05T12:00:00Z")
    FinancialTransaction.objects.create(**common, transaction_type="income", amount=Decimal("500.00"), payment_status="pending")
    FinancialTransaction.objects.create(**common, transaction_type="expense", amount=Decimal("200.00"), payment_status="pending")
    FinancialTransaction.objects.create(**common, transaction_type="expense", amount=Decimal("300.00"), paid_amount=Decimal("300.00"), payment_status="paid", paid_at="2026-07-06T12:00:00Z")
    return client, user


@pytest.mark.django_db
def test_summary_performance_query_count(perf_context):
    client, _ = perf_context
    with CaptureQueriesContext(connection) as queries:
        response = client.get("/api/v1/finances/summary/", {"start_date": "2026-07-01", "end_date": "2026-07-31"})
    assert response.status_code == 200
    assert len(queries) <= 2
    data = response.data
    assert Decimal(data["received"]) == Decimal("1000.00")
    assert Decimal(data["paid_expenses"]) == Decimal("300.00")
    assert Decimal(data["receivable"]) == Decimal("500.00")
    assert Decimal(data["payable"]) == Decimal("200.00")
