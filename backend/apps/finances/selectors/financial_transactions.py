"""Selectors de transações financeiras e isolamento multi-tenant."""

from __future__ import annotations

from datetime import date

from django.db.models import Q

from apps.finances.models import FinancialTransaction


def transactions_accessible_to(user):
    queryset = FinancialTransaction.objects.select_related(
        "patient", "appointment", "subscription", "therapist"
    )
    if not user or user.is_anonymous:
        return queryset.none()
    if user.is_admin_role or user.is_secretary:
        return queryset
    return queryset.filter(therapist=user)


def transaction_for_user(*, user, transaction_id):
    return transactions_accessible_to(user).filter(pk=transaction_id).first()


def transactions_for_owner(*, owner):
    return FinancialTransaction.objects.filter(therapist=owner).select_related("patient")


def transactions_for_owner_period(*, owner, start: date, end: date):
    return transactions_for_owner(owner=owner).filter(
        Q(due_date__range=(start, end))
        | Q(paid_at__date__range=(start, end))
        | Q(created_at__date__range=(start, end))
    )


def pending_transactions(*, user, patient_id=None):
    queryset = transactions_accessible_to(user).filter(
        payment_status__in=[
            FinancialTransaction.PaymentStatus.PENDING,
            FinancialTransaction.PaymentStatus.PARTIAL,
        ]
    )
    if patient_id:
        queryset = queryset.filter(patient_id=patient_id)
    return queryset.order_by("due_date", "created_at")


def transaction_for_appointment(*, appointment):
    return FinancialTransaction.objects.filter(
        appointment=appointment, source=FinancialTransaction.Source.APPOINTMENT
    ).first()


def transactions_for_admin(*, user):
    queryset = FinancialTransaction.objects.select_related("therapist", "patient", "appointment")
    return queryset if user.is_superuser else queryset.filter(therapist=user)
