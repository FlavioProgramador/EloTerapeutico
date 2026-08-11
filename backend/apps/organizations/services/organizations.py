"""Casos de uso transacionais de organizações."""

from __future__ import annotations

import uuid

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.organizations.models import (
    Organization,
    OrganizationMembership,
    OrganizationSettings,
    ProfessionalProfile,
)

from .audit import audit_organization_action


def _unique_slug(name: str) -> str:
    base = slugify(name)[:140] or "organizacao"
    candidate = base
    while Organization.objects.filter(slug=candidate).exists():
        candidate = f"{base}-{uuid.uuid4().hex[:8]}"
    return candidate


@transaction.atomic
def create_organization(*, actor, data: dict, request=None) -> Organization:
    name = str(data.get("name") or "").strip()
    if not name:
        raise ValueError("O nome da organização é obrigatório.")

    organization = Organization.objects.create(
        name=name,
        slug=_unique_slug(name),
        legal_name=str(data.get("legal_name") or "").strip(),
        organization_type=data.get("organization_type", Organization.Type.INDIVIDUAL),
        document=str(data.get("document") or "").strip(),
        email=str(data.get("email") or "").strip().lower(),
        phone=str(data.get("phone") or "").strip(),
        timezone=data.get("timezone") or "America/Sao_Paulo",
        created_by=actor,
        onboarding_status=Organization.OnboardingStatus.IN_PROGRESS,
        onboarding_step=1,
    )
    has_default = OrganizationMembership.objects.filter(
        user=actor,
        is_default=True,
    ).exists()
    membership = OrganizationMembership.objects.create(
        organization=organization,
        user=actor,
        role=OrganizationMembership.Role.OWNER,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=not has_default,
        joined_at=timezone.now(),
    )
    OrganizationSettings.objects.create(
        organization=organization,
        default_timezone=organization.timezone,
        business_name_on_documents=organization.name,
    )
    ProfessionalProfile.objects.create(
        membership=membership,
        display_name=getattr(actor, "display_name", "") or actor.full_name,
        professional_title=getattr(actor, "profession", ""),
        council_type="CRP" if getattr(actor, "crp_number", "") else "",
        council_number=getattr(actor, "crp_number", ""),
        specialties=[getattr(actor, "specialty", "")] if getattr(actor, "specialty", "") else [],
        bio=getattr(actor, "bio", ""),
        phone=getattr(actor, "phone", ""),
        public_email=actor.email,
        default_appointment_duration=getattr(actor, "default_session_duration", 50),
        default_session_value=getattr(actor, "default_session_value", 0),
        accepts_online=getattr(actor, "default_modality", "") in {"online", "hybrid"},
        accepts_in_person=getattr(actor, "default_modality", "in_person") in {"in_person", "hybrid"},
    )
    audit_organization_action(
        action="CREATE",
        actor=actor,
        organization=organization,
        request=request,
        metadata={"organization_type": organization.organization_type},
    )
    return organization


@transaction.atomic
def update_organization(*, actor, organization: Organization, data: dict, request=None) -> Organization:
    editable = {
        "name",
        "legal_name",
        "organization_type",
        "document",
        "email",
        "phone",
        "timezone",
    }
    for field in editable:
        if field in data:
            value = data[field]
            if isinstance(value, str):
                value = value.strip()
            setattr(organization, field, value)
    organization.save(update_fields=[*editable, "updated_at"])
    audit_organization_action(
        action="UPDATE",
        actor=actor,
        organization=organization,
        request=request,
    )
    return organization


@transaction.atomic
def activate_organization(*, actor, organization: Organization) -> OrganizationMembership:
    membership = OrganizationMembership.objects.select_for_update().get(
        organization=organization,
        user=actor,
        status=OrganizationMembership.Status.ACTIVE,
    )
    OrganizationMembership.objects.filter(user=actor, is_default=True).exclude(
        pk=membership.pk
    ).update(is_default=False)
    if not membership.is_default:
        membership.is_default = True
        membership.save(update_fields=["is_default", "updated_at"])
    return membership


@transaction.atomic
def archive_organization(*, actor, organization: Organization, request=None) -> Organization:
    organization.status = Organization.Status.ARCHIVED
    organization.save(update_fields=["status", "updated_at"])
    audit_organization_action(
        action="DELETE",
        actor=actor,
        organization=organization,
        request=request,
        metadata={"soft_delete": True},
    )
    return organization
