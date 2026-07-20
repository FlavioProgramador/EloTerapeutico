from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.finances.models import FinancialTransaction
from apps.users.models import User


@pytest.fixture
def financial_user(db):
    return User.objects.create_user(
        email="financeiro-resumo@example.com",
        full_name="Profissional Financeiro",
        password="safe-test-password",
        role=User.Role.THERAPIST,
        crp_number="06/111111",
    )


@pytest.fixture
def financial_client(financial_user):
    client = APIClient()
    client.force_authenticate(financial_user)
    return client


@pytest.mark.django_db
def test_summary_calculates_projected_balance(financial_client, financial_user):
    common = {"therapist": financial_user, "due_date": date(2026, 7, 10)}
    FinancialTransaction.objects.create(
        **common,
        transaction_type="income",
        amount=Decimal("1000.00"),
        paid_amount=Decimal("1000.00"),
        payment_status="paid",
        paid_at="2026-07-05T12:00:00Z",
    )
    FinancialTransaction.objects.create(
        **common,
        transaction_type="income",
        amount=Decimal("500.00"),
        payment_status="pending",
    )
    FinancialTransaction.objects.create(
        **common,
        transaction_type="expense",
        amount=Decimal("200.00"),
        payment_status="pending",
    )

    response = financial_client.get(
        "/api/v1/finances/summary/",
        {"start_date": "2026-07-01", "end_date": "2026-07-31"},
    )

    assert response.status_code == 200
    assert Decimal(response.data["received"]) == Decimal("1000.00")
    assert Decimal(response.data["receivable"]) == Decimal("500.00")
    assert Decimal(response.data["payable"]) == Decimal("200.00")
    assert Decimal(response.data["projected_balance"]) == Decimal("1300.00")


@pytest.mark.django_db
def test_summary_rejects_invalid_period(financial_client):
    response = financial_client.get(
        "/api/v1/finances/summary/",
        {"start_date": "2026-08-01", "end_date": "2026-07-01"},
    )
    assert response.status_code == 400
