"""Consultas de convites por organização."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.organizations.models import OrganizationInvitation


def list_invitations(*, organization) -> QuerySet[OrganizationInvitation]:
    return OrganizationInvitation.objects.filter(organization=organization).select_related(
        "invited_by", "accepted_by", "organization"
    )


def get_invitation(*, organization, invitation_id) -> OrganizationInvitation:
    return list_invitations(organization=organization).get(pk=invitation_id)


def get_invitation_by_hash(*, token_hash: str) -> OrganizationInvitation:
    return OrganizationInvitation.objects.select_related(
        "organization", "invited_by", "accepted_by"
    ).get(token_hash=token_hash)
