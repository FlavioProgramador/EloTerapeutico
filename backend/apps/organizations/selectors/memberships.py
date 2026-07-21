"""Consultas de memberships com isolamento por organização."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.organizations.models import OrganizationMembership


def list_memberships(*, organization) -> QuerySet[OrganizationMembership]:
    return (
        OrganizationMembership.objects.filter(organization=organization)
        .select_related("user", "invited_by", "organization")
        .order_by("user__full_name")
    )


def get_membership(*, organization, membership_id) -> OrganizationMembership:
    return list_memberships(organization=organization).get(pk=membership_id)


def get_active_membership(*, organization, user) -> OrganizationMembership:
    return OrganizationMembership.objects.select_related("organization", "user").get(
        organization=organization,
        user=user,
        status=OrganizationMembership.Status.ACTIVE,
    )


def list_active_memberships_for_user(*, user) -> QuerySet[OrganizationMembership]:
    return OrganizationMembership.objects.filter(
        user=user,
        status=OrganizationMembership.Status.ACTIVE,
        organization__status="active",
    ).select_related("organization", "user")
