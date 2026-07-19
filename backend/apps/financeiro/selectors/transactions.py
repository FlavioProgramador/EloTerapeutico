"""Consultas reutilizáveis do domínio financeiro."""

from decimal import Decimal

from django.db.models import Sum

from apps.scheduling.models import Appointment

from ..models import FinancialTransaction


def transactions_accessible_to(user):
    queryset = FinancialTransaction.objects.select_related(
        "patient",
        "appointment",
        "therapist",
    )
    if not user or user.is_anonymous:
        return queryset.none()
    if user.is_admin_role or user.is_secretary:
        return queryset
    return queryset.filter(therapist=user)


def pending_transactions(*, user, patient_id=None):
    queryset = transactions_accessible_to(user).filter(payment_status=FinancialTransaction.PaymentStatus.PENDING)
    if patient_id:
        queryset = queryset.filter(patient_id=patient_id)
    return queryset.order_by("due_date", "created_at")


def monthly_summary(*, therapist, year: int, month: int) -> dict:
    queryset = FinancialTransaction.objects.filter(
        therapist=therapist,
        created_at__year=year,
        created_at__month=month,
    )
    paid = queryset.filter(payment_status=FinancialTransaction.PaymentStatus.PAID)
    income = paid.filter(transaction_type=FinancialTransaction.TransactionType.INCOME).aggregate(total=Sum("amount"))[
        "total"
    ] or Decimal("0.00")
    expense = paid.filter(transaction_type=FinancialTransaction.TransactionType.EXPENSE).aggregate(total=Sum("amount"))[
        "total"
    ] or Decimal("0.00")
    pending = queryset.filter(payment_status=FinancialTransaction.PaymentStatus.PENDING).aggregate(total=Sum("amount"))[
        "total"
    ] or Decimal("0.00")
    return {
        "year": year,
        "month": month,
        "total_income": income,
        "total_expense": expense,
        "balance": income - expense,
        "total_pending": pending,
        "transaction_count": queryset.count(),
    }


def unbilled_appointments_for(user):
    if not user or user.is_anonymous or not user.is_therapist:
        return Appointment.objects.none()
    return (
        Appointment.objects.filter(
            therapist=user,
            status=Appointment.Status.CONFIRMED,
        )
        .exclude(financial_transactions__isnull=False)
        .select_related("patient")
        .order_by("-start_time")
    )
