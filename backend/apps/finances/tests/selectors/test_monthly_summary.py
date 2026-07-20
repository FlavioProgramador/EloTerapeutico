from datetime import date
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.finances.models import FinancialTransaction
from apps.finances.selectors import monthly_summary as selector_monthly_summary
from apps.users.models import User


@pytest.fixture
def summary_context(db):
    therapist = User.objects.create_user(
        email="summary-therapist@example.com",
        full_name="Profissional de Resumo",
        password="safe-test-password",
        role=User.Role.THERAPIST,
    )
    other_therapist = User.objects.create_user(
        email="other-summary-therapist@example.com",
        full_name="Outro Profissional",
        password="safe-test-password",
        role=User.Role.THERAPIST,
    )
    FinancialTransaction.objects.create(
        therapist=therapist, transaction_type="income", amount=Decimal("1000.00"),
        paid_amount=Decimal("1000.00"), payment_status="paid", due_date=date(2026, 7, 10), paid_at="2026-07-05T12:00:00Z",
    )
    FinancialTransaction.objects.create(
        therapist=therapist, transaction_type="income", amount=Decimal("500.00"), payment_status="pending", due_date=date(2026, 7, 12),
    )
    FinancialTransaction.objects.create(
        therapist=therapist, transaction_type="expense", amount=Decimal("200.00"), payment_status="pending", due_date=date(2026, 7, 15),
    )
    FinancialTransaction.objects.create(
        therapist=therapist, transaction_type="expense", amount=Decimal("300.00"), paid_amount=Decimal("300.00"), payment_status="paid", due_date=date(2026, 7, 20), paid_at="2026-07-06T12:00:00Z",
    )
    FinancialTransaction.objects.create(
        therapist=therapist, transaction_type="income", amount=Decimal("400.00"), paid_amount=Decimal("100.00"), payment_status="partial", due_date=date(2026, 7, 25),
    )
    FinancialTransaction.objects.create(
        therapist=other_therapist, transaction_type="income", amount=Decimal("2000.00"), paid_amount=Decimal("2000.00"), payment_status="paid", due_date=date(2026, 7, 10),
    )
    return therapist, other_therapist


@pytest.mark.django_db
def test_selector_monthly_summary_correctness_and_performance(summary_context):
    therapist, _ = summary_context
    with CaptureQueriesContext(connection) as queries:
        result = selector_monthly_summary(therapist=therapist, year=2026, month=7)
    assert len(queries) == 1
    assert result["total_income"] == Decimal("1000.00")
    assert result["total_expense"] == Decimal("300.00")
    assert result["balance"] == Decimal("700.00")
    assert result["total_pending"] == Decimal("1000.00")
    assert result["transaction_count"] == 5
