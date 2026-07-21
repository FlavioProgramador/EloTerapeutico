"""Selectors financeiros consumidos pelo módulo de relatórios."""

from django.db.models import Q

from apps.finances.selectors import (
    monthly_subscriptions_accessible_to,
    transactions_accessible_to,
)
from apps.organizations.models import OrganizationMembership
from apps.scheduling.models import PatientPackage


def transactions_for_period(*, user, organization, start, end):
    return transactions_accessible_to(user, organization=organization).filter(
        Q(due_date__range=(start, end))
        | Q(paid_at__date__range=(start, end))
        | Q(created_at__date__range=(start, end))
    )


def all_transactions_for_user(*, user, organization):
    return transactions_accessible_to(user, organization=organization)


def active_subscriptions_for_user(*, user, organization):
    return monthly_subscriptions_accessible_to(
        user,
        organization=organization,
        status="active",
    )


def active_packages_for_user(*, user, organization):
    membership = OrganizationMembership.objects.filter(
        organization=organization,
        user=user,
        status=OrganizationMembership.Status.ACTIVE,
    ).first()
    queryset = PatientPackage.objects.filter(
        organization=organization,
        status=PatientPackage.Status.ACTIVE,
    ).select_related("patient", "therapist")
    if membership is None:
        return queryset.none()
    if membership.role == OrganizationMembership.Role.THERAPIST:
        return queryset.filter(therapist=user)
    return queryset


# Fachadas legadas mantidas para adapters antigos.
def transactions_for_period_legacy(*, owner, start, end):
    return transactions_accessible_to(owner).filter(
        Q(due_date__range=(start, end))
        | Q(paid_at__date__range=(start, end))
        | Q(created_at__date__range=(start, end))
    )


def all_transactions_for_owner(*, owner):
    return transactions_accessible_to(owner)


def active_subscriptions_for_owner(*, owner):
    return monthly_subscriptions_accessible_to(owner, status="active")


def active_packages_for_owner(*, owner):
    return PatientPackage.objects.filter(
        therapist=owner,
        status=PatientPackage.Status.ACTIVE,
    )
