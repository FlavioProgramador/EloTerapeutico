"""Selectors de mensalidades recorrentes por organização."""

from apps.finances.models import MonthlySubscription
from apps.organizations.models import OrganizationMembership

FULL_FINANCE_ROLES = {
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

    memberships = OrganizationMembership.objects.filter(
        user=user,
        status=OrganizationMembership.Status.ACTIVE,
    )
    if organization is not None:
        membership = memberships.filter(organization=organization).first()
        if membership is None:
            queryset = queryset.none()
        else:
            queryset = queryset.filter(organization=organization)
            if membership.role == OrganizationMembership.Role.THERAPIST:
                queryset = queryset.filter(therapist=user)
            elif membership.role not in FULL_FINANCE_ROLES:
                queryset = queryset.none()
    else:
        full_scope_orgs = memberships.filter(
            role__in=FULL_FINANCE_ROLES,
        ).values_list("organization_id", flat=True)
        therapist_orgs = memberships.filter(
            role=OrganizationMembership.Role.THERAPIST,
        ).values_list("organization_id", flat=True)
        from django.db.models import Q

        queryset = queryset.filter(
            Q(organization_id__in=full_scope_orgs)
            | Q(organization_id__in=therapist_orgs, therapist=user)
        )
    if status:
        queryset = queryset.filter(status=status)
    return queryset


def active_monthly_subscriptions_for(*, owner, organization=None):
    queryset = MonthlySubscription.objects.filter(
        therapist=owner,
        status=MonthlySubscription.Status.ACTIVE,
    ).select_related("organization", "patient")
    return queryset.filter(organization=organization) if organization else queryset
