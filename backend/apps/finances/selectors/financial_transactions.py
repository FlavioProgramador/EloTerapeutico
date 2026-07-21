"""Selectors de transações financeiras com isolamento por organização."""

from __future__ import annotations

from datetime import date

from django.db.models import Q

from apps.finances.models import FinancialTransaction
from apps.organizations.models import OrganizationMembership

FINANCE_ROLES = {
    OrganizationMembership.Role.OWNER,
    OrganizationMembership.Role.ADMIN,
    OrganizationMembership.Role.FINANCE,
}


def transactions_accessible_to(user, *, organization=None):
    queryset = FinancialTransaction.objects.select_related(
        "organization",
        "patient",
        "appointment",
        "subscription",
        "therapist",
    )
    if not user or user.is_anonymous:
        return queryset.none()
    if organization is not None:
        allowed = OrganizationMembership.objects.filter(
            organization=organization,
            user=user,
            status=OrganizationMembership.Status.ACTIVE,
            role__in=FINANCE_ROLES,
        ).exists()
        return queryset.filter(organization=organization) if allowed else queryset.none()
    organization_ids = OrganizationMembership.objects.filter(
        user=user,
        status=OrganizationMembership.Status.ACTIVE,
        role__in=FINANCE_ROLES,
    ).values_list("organization_id", flat=True)
    return queryset.filter(organization_id__in=organization_ids)


def transaction_for_user(*, user, transaction_id, organization=None):
    return transactions_accessible_to(user, organization=organization).filter(
        pk=transaction_id
    ).first()


def transactions_for_owner(*, owner, organization=None):
    queryset = FinancialTransaction.objects.filter(therapist=owner).select_related(
        "organization",
        "patient",
    )
    return queryset.filter(organization=organization) if organization else queryset


def transactions_for_owner_period(*, owner, start: date, end: date, organization=None):
    return transactions_for_owner(owner=owner, organization=organization).filter(
        Q(due_date__range=(start, end))
        | Q(paid_at__date__range=(start, end))
        | Q(created_at__date__range=(start, end))
    )


def pending_transactions(*, user, patient_id=None, organization=None):
    queryset = transactions_accessible_to(user, organization=organization).filter(
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
        organization=appointment.organization,
        appointment=appointment,
        source=FinancialTransaction.Source.APPOINTMENT,
    ).first()


def transactions_for_admin(*, user, organization=None):
    queryset = FinancialTransaction.objects.select_related(
        "organization",
        "therapist",
        "patient",
        "appointment",
    )
    if organization is not None:
        return queryset.filter(organization=organization)
    return queryset if user.is_superuser else transactions_accessible_to(user)
