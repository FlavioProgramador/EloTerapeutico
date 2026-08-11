"""Leitura agregada do progresso de onboarding."""

from __future__ import annotations

from apps.organizations.models import OrganizationMembership


def get_onboarding_context(*, organization, user) -> dict[str, object]:
    membership = OrganizationMembership.objects.select_related(
        "organization", "user"
    ).get(organization=organization, user=user)
    profile = getattr(membership, "professional_profile", None)
    settings = getattr(organization, "settings", None)
    return {
        "organization": organization,
        "membership": membership,
        "professional_profile": profile,
        "settings": settings,
        "status": organization.onboarding_status,
        "step": organization.onboarding_step,
        "completed_at": organization.onboarding_completed_at,
    }
