"""Selectors de mensalidades recorrentes por organização."""

from apps.finances.models import MonthlySubscription
from apps.organizations.models import OrganizationMembership

FINANCE_ROLES = {
    OrganizationMembership.Role.OWNER,
    OrganizationMembership.Role.ADMIN,
    OrganizationMembership.Role.FINANCE,
}


def monthly_subscriptions_accessible_to(user, *, organization=None, status=None):
    queryset = MonthlySubscription.objects.select_related(
        "organization",
        "patient",
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
        queryset = queryset.filter(organization=organization) if allowed else queryset.none()
    else:
        organization_ids = OrganizationMembership.objects.filter(
            user=user,
            status=OrganizationMembership.Status.ACTIVE,
            role__in=FINANCE_ROLES,
        ).values_list("organization_id", flat=True)
        queryset = queryset.filter(organization_id__in=organization_ids)
    if status:
        queryset = queryset.filter(status=status)
    return queryset


def active_monthly_subscriptions_for(*, owner, organization=None):
    queryset = MonthlySubscription.objects.filter(
        therapist=owner,
        status=MonthlySubscription.Status.ACTIVE,
    ).select_related("organization", "patient")
    return queryset.filter(organization=organization) if organization else queryset
