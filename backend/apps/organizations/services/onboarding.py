"""Casos de uso do onboarding persistido da organização."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.billing.models import Subscription
from apps.organizations.exceptions import OnboardingIncompleteError
from apps.organizations.models import Organization, OrganizationSettings, ProfessionalProfile
from apps.scheduling.telemedicine_config import get_telemedicine_config

from .audit import audit_organization_action


def _validate_telemedicine_activation(*, actor) -> None:
    config = get_telemedicine_config()
    if not config.enabled or not config.provider_configured:
        raise ValidationError(
            {
                "allow_telemedicine": (
                    "O atendimento online ainda não está disponível para esta organização."
                )
            }
        )
    subscription = (
        Subscription.objects.select_related("plan")
        .filter(
            user=actor,
            status__in=[
                Subscription.Status.TRIALING,
                Subscription.Status.ACTIVE,
                Subscription.Status.PAST_DUE,
            ],
        )
        .order_by("-created_at")
        .first()
    )
    if not (
        subscription
        and subscription.has_access
        and subscription.plan.has_telemedicine
    ):
        raise ValidationError(
            {"allow_telemedicine": "O plano atual não inclui atendimento online."}
        )


@transaction.atomic
def update_onboarding(
    *, actor, organization: Organization, membership, data: dict, request=None
) -> dict[str, object]:
    organization_data = data.get("organization") or {}
    settings_data = data.get("settings") or {}
    profile_data = data.get("professional_profile") or {}

    if settings_data.get("allow_telemedicine") is True:
        _validate_telemedicine_activation(actor=actor)

    for field in {
        "name",
        "legal_name",
        "organization_type",
        "document",
        "email",
        "phone",
        "timezone",
    }:
        if field in organization_data:
            value = organization_data[field]
            if isinstance(value, str):
                value = value.strip()
            setattr(organization, field, value)

    step = data.get("step")
    if step is not None:
        organization.onboarding_step = max(1, min(int(step), 6))
    organization.onboarding_status = Organization.OnboardingStatus.IN_PROGRESS
    organization.save()

    settings_obj, _ = OrganizationSettings.objects.get_or_create(
        organization=organization,
        defaults={"default_timezone": organization.timezone},
    )
    for field in {
        "default_timezone",
        "default_currency",
        "default_appointment_duration",
        "minimum_booking_notice_minutes",
        "maximum_booking_days",
        "cancellation_notice_hours",
        "allow_online_booking",
        "allow_patient_portal",
        "allow_telemedicine",
        "send_appointment_reminders",
        "reminder_hours_before",
        "business_name_on_documents",
        "document_header",
        "document_footer",
    }:
        if field in settings_data:
            setattr(settings_obj, field, settings_data[field])
    settings_obj.save()

    profile, _ = ProfessionalProfile.objects.get_or_create(
        membership=membership,
        defaults={"display_name": membership.user.full_name},
    )
    for field in {
        "display_name",
        "professional_title",
        "council_type",
        "council_number",
        "council_region",
        "specialties",
        "bio",
        "phone",
        "public_email",
        "default_appointment_duration",
        "default_session_value",
        "accepts_online",
        "accepts_in_person",
        "is_public",
    }:
        if field in profile_data:
            setattr(profile, field, profile_data[field])
    profile.save()

    audit_organization_action(
        action="UPDATE",
        actor=actor,
        organization=organization,
        request=request,
        metadata={"onboarding_step": organization.onboarding_step},
    )
    return {
        "organization": organization,
        "settings": settings_obj,
        "professional_profile": profile,
    }


@transaction.atomic
def complete_onboarding(
    *, actor, organization: Organization, membership, request=None
) -> Organization:
    settings_obj = getattr(organization, "settings", None)
    profile = getattr(membership, "professional_profile", None)
    missing: list[str] = []
    if not organization.name.strip():
        missing.append("organization.name")
    if not organization.timezone.strip():
        missing.append("organization.timezone")
    if settings_obj is None:
        missing.append("settings")
    if membership.role in {"owner", "therapist"} and profile is None:
        missing.append("professional_profile")
    if profile is not None and not profile.display_name.strip():
        missing.append("professional_profile.display_name")
    if missing:
        raise OnboardingIncompleteError(detail={"missing_fields": missing})

    organization.onboarding_status = Organization.OnboardingStatus.COMPLETED
    organization.onboarding_step = 6
    organization.onboarding_completed_at = timezone.now()
    organization.save(
        update_fields=[
            "onboarding_status",
            "onboarding_step",
            "onboarding_completed_at",
            "updated_at",
        ]
    )
    audit_organization_action(
        action="UPDATE",
        actor=actor,
        organization=organization,
        request=request,
        metadata={"onboarding_completed": True},
    )
    return organization
