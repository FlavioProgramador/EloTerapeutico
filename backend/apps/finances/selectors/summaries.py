"""Agregações financeiras canônicas."""

from __future__ import annotations

from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.finances.models import FinancialTransaction
from apps.finances.selectors.financial_transactions import transactions_accessible_to

MONEY_FIELD = DecimalField(max_digits=12, decimal_places=2)
ZERO_MONEY = Value(Decimal("0.00"), output_field=MONEY_FIELD)


def _sum(field_name: str, query_filter: Q):
    return Coalesce(
        Sum(field_name, filter=query_filter),
        ZERO_MONEY,
        output_field=MONEY_FIELD,
    )


def financial_summary(*, user, start_date: date, end_date: date) -> dict:
    today = timezone.localdate()
    period_filter = Q(due_date__range=(start_date, end_date)) | Q(
        paid_at__date__range=(start_date, end_date)
    )
    queryset = (
        transactions_accessible_to(user)
        .filter(period_filter)
        .exclude(
            payment_status__in=[
                FinancialTransaction.PaymentStatus.CANCELLED,
                FinancialTransaction.PaymentStatus.REFUNDED,
            ]
        )
    )
    open_filter = Q(
        payment_status__in=[
            FinancialTransaction.PaymentStatus.PENDING,
            FinancialTransaction.PaymentStatus.PARTIAL,
        ]
    )
    paid_filter = Q(payment_status=FinancialTransaction.PaymentStatus.PAID)
    received_filter = paid_filter & Q(
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        paid_at__date__range=(start_date, end_date),
    )
    paid_expenses_filter = paid_filter & Q(
        transaction_type=FinancialTransaction.TransactionType.EXPENSE,
        paid_at__date__range=(start_date, end_date),
    )
    receivable_filter = open_filter & Q(
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        due_date__range=(start_date, end_date),
    )
    payable_filter = open_filter & Q(
        transaction_type=FinancialTransaction.TransactionType.EXPENSE,
        due_date__range=(start_date, end_date),
    )
    overdue_filter = open_filter & Q(due_date__lt=today)
    metrics = queryset.aggregate(
        received=_sum("amount", received_filter),
        received_count=Count("id", filter=received_filter),
        paid_expenses=_sum("amount", paid_expenses_filter),
        paid_expenses_count=Count("id", filter=paid_expenses_filter),
        receivable_amount=_sum("amount", receivable_filter),
        receivable_paid=_sum("paid_amount", receivable_filter),
        receivable_count=Count("id", filter=receivable_filter),
        payable_amount=_sum("amount", payable_filter),
        payable_paid=_sum("paid_amount", payable_filter),
        payable_count=Count("id", filter=payable_filter),
        overdue_amount=_sum("amount", overdue_filter),
        overdue_paid=_sum("paid_amount", overdue_filter),
        overdue_receivable_count=Count(
            "id",
            filter=overdue_filter
            & Q(transaction_type=FinancialTransaction.TransactionType.INCOME),
        ),
        overdue_payable_count=Count(
            "id",
            filter=overdue_filter
            & Q(transaction_type=FinancialTransaction.TransactionType.EXPENSE),
        ),
        transaction_count=Count("id"),
    )
    received = metrics["received"]
    paid_expenses = metrics["paid_expenses"]
    receivable = metrics["receivable_amount"] - metrics["receivable_paid"]
    payable = metrics["payable_amount"] - metrics["payable_paid"]
    overdue = metrics["overdue_amount"] - metrics["overdue_paid"]
    return {
        "start_date": start_date,
        "end_date": end_date,
        "received": received,
        "received_count": metrics["received_count"],
        "receivable": receivable,
        "receivable_count": metrics["receivable_count"],
        "payable": payable,
        "payable_count": metrics["payable_count"],
        "paid_expenses": paid_expenses,
        "paid_expenses_count": metrics["paid_expenses_count"],
        "overdue": overdue,
        "overdue_receivable_count": metrics["overdue_receivable_count"],
        "overdue_payable_count": metrics["overdue_payable_count"],
        "projected_balance": received + receivable - paid_expenses - payable,
        "transaction_count": metrics["transaction_count"],
        "total_income": received,
        "total_expense": paid_expenses,
        "balance": received - paid_expenses,
        "total_pending": receivable + payable,
    }


def monthly_summary(*, therapist, year: int, month: int) -> dict:
    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])
    summary = financial_summary(
        user=therapist, start_date=start_date, end_date=end_date
    )
    return {
        "year": year,
        "month": month,
        "total_income": summary["total_income"],
        "total_expense": summary["total_expense"],
        "balance": summary["balance"],
        "total_pending": summary["total_pending"],
        "transaction_count": summary["transaction_count"],
    }


def admin_changelist_summary(queryset) -> dict:
    paid = Q(payment_status=FinancialTransaction.PaymentStatus.PAID)
    open_status = Q(
        payment_status__in=[
            FinancialTransaction.PaymentStatus.PENDING,
            FinancialTransaction.PaymentStatus.PARTIAL,
        ]
    )
    values = queryset.aggregate(
        total_income=_sum(
            "amount", paid & Q(transaction_type=FinancialTransaction.TransactionType.INCOME)
        ),
        total_expense=_sum(
            "amount", paid & Q(transaction_type=FinancialTransaction.TransactionType.EXPENSE)
        ),
        pending_amount=_sum("amount", open_status),
        pending_paid=_sum("paid_amount", open_status),
        total_transactions=Count("id"),
    )
    pending = values["pending_amount"] - values["pending_paid"]
    return {
        "total_income": values["total_income"],
        "total_expense": values["total_expense"],
        "balance": values["total_income"] - values["total_expense"],
        "total_pending": pending,
        "total_transactions": values["total_transactions"],
    }
