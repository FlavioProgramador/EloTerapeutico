"""Cobranças elegíveis para automações de comunicação."""

from apps.finances.models import FinancialTransaction


def transactions_requiring_reminder(*, today, due_limit):
    return FinancialTransaction.objects.filter(
        transaction_type=FinancialTransaction.TransactionType.INCOME,
        payment_status__in=[
            FinancialTransaction.PaymentStatus.PENDING,
            FinancialTransaction.PaymentStatus.PARTIAL,
        ],
        patient__isnull=False,
        due_date__isnull=False,
        due_date__lte=due_limit,
    ).select_related("therapist", "patient")
