"""Adição controlada de usuários já cadastrados à organização."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.organizations.models import OrganizationMembership, ProfessionalProfile

from .audit import audit_organization_action


@transaction.atomic
def add_existing_member(
    *, actor, organization, email: str, role: str, request=None
) -> OrganizationMembership:
    user_model = get_user_model()
    user = user_model.objects.get(email__iexact=email.strip())
    membership, _ = OrganizationMembership.objects.update_or_create(
        organization=organization,
        user=user,
        defaults={
            "role": role,
            "status": OrganizationMembership.Status.ACTIVE,
            "invited_by": actor,
            "joined_at": timezone.now(),
        },
    )
    if role in {
        OrganizationMembership.Role.OWNER,
        OrganizationMembership.Role.ADMIN,
        OrganizationMembership.Role.THERAPIST,
    }:
        ProfessionalProfile.objects.get_or_create(
            membership=membership,
            defaults={"display_name": user.full_name},
        )
    audit_organization_action(
        action="CREATE",
        actor=actor,
        organization=organization,
        request=request,
        metadata={"membership_id": str(membership.pk), "role": role},
    )
    return membership
