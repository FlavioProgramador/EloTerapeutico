from datetime import date
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.financeiro.models import FinancialTransaction
from apps.financeiro.selectors.transactions import monthly_summary as selector_monthly_summary
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

    # 1. Paid Income for therapist (created in July 2026, due on July 10, 2026)
    FinancialTransaction.objects.create(
        therapist=therapist,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=Decimal("1000.00"),
        paid_amount=Decimal("1000.00"),
        payment_status=FinancialTransaction.PaymentStatus.PAID,
        due_date=date(2026, 7, 10),
        paid_at="2026-07-05T12:00:00Z",
    )
    # 2. Pending Income for therapist (created in July 2026, due on July 12, 2026)
    FinancialTransaction.objects.create(
        therapist=therapist,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=Decimal("500.00"),
        payment_status=FinancialTransaction.PaymentStatus.PENDING,
        due_date=date(2026, 7, 12),
    )
    # 3. Pending Expense for therapist (created in July 2026, due on July 15, 2026)
    FinancialTransaction.objects.create(
        therapist=therapist,
        transaction_type=FinancialTransaction.TransactionType.EXPENSE,
        amount=Decimal("200.00"),
        payment_status=FinancialTransaction.PaymentStatus.PENDING,
        due_date=date(2026, 7, 15),
    )
    # 4. Paid Expense for therapist (created in July 2026, due on July 20, 2026)
    FinancialTransaction.objects.create(
        therapist=therapist,
        transaction_type=FinancialTransaction.TransactionType.EXPENSE,
        amount=Decimal("300.00"),
        paid_amount=Decimal("300.00"),
        payment_status=FinancialTransaction.PaymentStatus.PAID,
        due_date=date(2026, 7, 20),
        paid_at="2026-07-06T12:00:00Z",
    )
    # 5. Partial Paid Income for therapist (created in July 2026, due on July 25, 2026)
    FinancialTransaction.objects.create(
        therapist=therapist,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=Decimal("400.00"),
        paid_amount=Decimal("100.00"),
        payment_status=FinancialTransaction.PaymentStatus.PARTIAL,
        due_date=date(2026, 7, 25),
    )

    # 6. Some transaction for another therapist (should be isolated)
    FinancialTransaction.objects.create(
        therapist=other_therapist,
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        amount=Decimal("2000.00"),
        paid_amount=Decimal("2000.00"),
        payment_status=FinancialTransaction.PaymentStatus.PAID,
        due_date=date(2026, 7, 10),
    )

    return therapist, other_therapist


@pytest.mark.django_db
def test_selector_monthly_summary_correctness_and_performance(summary_context):
    therapist, _ = summary_context

    with CaptureQueriesContext(connection) as queries:
        result = selector_monthly_summary(therapist=therapist, year=2026, month=7)

    # Performance assertion: exactly 1 database query
    assert len(queries) == 1

    # Correctness assertions based on creation date:
    # All 5 transactions for the therapist were created in July 2026 (auto_now_add).
    # Since selector filters by created_at, they are all included.
    assert result["year"] == 2026
    assert result["month"] == 7
    assert result["total_income"] == Decimal("1000.00")  # Only status='paid' is included in total_income
    assert result["total_expense"] == Decimal("300.00")  # Only status='paid' is included in total_expense
    assert result["balance"] == Decimal("700.00")
    # For selector, pending includes only PENDING (PARTIAL is not in selectors/transactions.py original pending filter):
    # Transaction 2 (PENDING): 500.00
    # Transaction 3 (PENDING): 200.00
    # Total pending = 500 + 200 = 700.00
    assert result["total_pending"] == Decimal("700.00")
    assert result["transaction_count"] == 5


@pytest.mark.django_db
def test_classmethod_monthly_summary_correctness_and_performance(summary_context):
    therapist, _ = summary_context

    with CaptureQueriesContext(connection) as queries:
        result = FinancialTransaction.monthly_summary(therapist=therapist, year=2026, month=7)

    # Performance assertion: exactly 1 database query
    assert len(queries) == 1

    # Correctness assertions based on due_date:
    # All 5 transactions have due_date in July 2026.
    assert result["year"] == 2026
    assert result["month"] == 7
    assert result["total_income"] == Decimal("1000.00")  # paid income
    assert result["total_expense"] == Decimal("300.00")  # paid expense
    assert result["balance"] == Decimal("700.00")
    # For classmethod, pending includes both PENDING and PARTIAL:
    # Transaction 2 (PENDING): 500.00
    # Transaction 3 (PENDING): 200.00
    # Transaction 5 (PARTIAL): 400.00
    # Total pending = 500 + 200 + 400 = 1100.00
    assert result["total_pending"] == Decimal("1100.00")
    assert result["transaction_count"] == 5
