"""Consultas de organizações visíveis ao usuário."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.organizations.models import Organization, OrganizationMembership


def list_user_organizations(*, user) -> QuerySet[Organization]:
    return (
        Organization.objects.filter(
            memberships__user=user,
            memberships__status=OrganizationMembership.Status.ACTIVE,
        )
        .distinct()
        .order_by("name")
    )


def get_visible_organization(*, user, organization_id) -> Organization:
    return list_user_organizations(user=user).get(pk=organization_id)
