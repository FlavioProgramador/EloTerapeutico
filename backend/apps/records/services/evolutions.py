"""Casos de uso transacionais do fluxo de evoluções clínicas."""

from __future__ import annotations

import json
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from ..evolution_security import sanitize_original_filename
from ..models import ClinicalDocument, Evolution, EvolutionClinicalData, EvolutionVersion

CLINICAL_PROFILE_FIELDS = (
    "session_time",
    "duration_minutes",
    "modality",
    "appointment_type",
    "emotional_state",
    "chief_complaint",
    "patient_report",
    "therapist_observations",
    "interventions",
    "perceived_evolution",
    "homework",
    "referrals",
    "next_steps",
)


def _snapshot(evolution: Evolution) -> dict[str, Any]:
    profile = getattr(evolution, "clinical_data", None)
    data: dict[str, Any] = {
        "appointment_id": evolution.appointment_id,
        "session_date": evolution.session_date.isoformat(),
        "content": evolution.content,
        "cid10": evolution.cid10,
        "is_confidential": evolution.is_confidential,
    }
    for field in CLINICAL_PROFILE_FIELDS:
        data[field] = getattr(profile, field, "") if profile else ""
    return data


@transaction.atomic
def create_evolution(*, patient, actor, validated_data: dict[str, Any]) -> Evolution:
    payload = dict(validated_data)
    payload.pop("content_format", None)
    payload.pop("confirm_appointment_date_override", None)
    clinical_data = payload.pop("clinical_data", {})

    evolution = Evolution.objects.create(
        patient=patient,
        created_by=actor,
        **payload,
    )
    EvolutionClinicalData.objects.create(
        evolution=evolution,
        updated_by=actor,
        **clinical_data,
    )
    return evolution


@transaction.atomic
def update_evolution(
    *,
    evolution: Evolution,
    actor,
    validated_data: dict[str, Any],
) -> Evolution:
    profile = getattr(evolution, "clinical_data", None)
    if evolution.created_by_id != actor.id:
        raise PermissionDenied("Somente o autor pode alterar esta evolução.")
    if not evolution.can_be_edited():
        raise ValidationError("Esta evolução não pode mais ser alterada diretamente.")
    if profile and profile.status != EvolutionClinicalData.Status.DRAFT:
        raise ValidationError("Apenas evoluções em rascunho podem ser alteradas.")

    payload = dict(validated_data)
    payload.pop("content_format", None)
    payload.pop("confirm_appointment_date_override", None)
    clinical_data = payload.pop("clinical_data", {})

    latest = evolution.versions.order_by("-version").first()
    EvolutionVersion.objects.create(
        evolution=evolution,
        version=(latest.version + 1) if latest else 1,
        snapshot=json.dumps(_snapshot(evolution), ensure_ascii=False, default=str),
        created_by=actor,
    )

    for field, value in payload.items():
        setattr(evolution, field, value)
    evolution.save()

    profile, _ = EvolutionClinicalData.objects.get_or_create(
        evolution=evolution,
        defaults={"updated_by": actor},
    )
    for field, value in clinical_data.items():
        setattr(profile, field, value)
    profile.updated_by = actor
    profile.save()
    return evolution


@transaction.atomic
def archive_evolution(*, evolution: Evolution, actor) -> None:
    if evolution.created_by_id != actor.id and not actor.is_admin_role:
        raise PermissionDenied("Você não pode arquivar esta evolução.")

    profile, _ = EvolutionClinicalData.objects.get_or_create(
        evolution=evolution,
        defaults={"updated_by": actor},
    )
    profile.updated_by = actor
    profile.save(update_fields=["updated_by", "updated_at"])
    profile.archive()


@transaction.atomic
def create_evolution_attachment(*, evolution: Evolution, actor, uploaded_file):
    profile = getattr(evolution, "clinical_data", None)
    if evolution.created_by_id != actor.id:
        raise PermissionDenied("Somente o autor pode adicionar anexos.")
    if not evolution.can_be_edited():
        raise ValidationError("Esta evolução não aceita novos anexos.")
    if profile and profile.status != EvolutionClinicalData.Status.DRAFT:
        raise ValidationError("Apenas rascunhos aceitam novos anexos.")

    return ClinicalDocument.objects.create(
        patient=evolution.patient,
        evolution=evolution,
        category=ClinicalDocument.Category.OTHER,
        file=uploaded_file,
        original_name=sanitize_original_filename(uploaded_file.name),
        description="Anexo protegido da evolução clínica",
        content_type=uploaded_file.content_type,
        size_bytes=uploaded_file.size,
        checksum=ClinicalDocument.calculate_checksum(uploaded_file),
        uploaded_by=actor,
    )


@transaction.atomic
def remove_evolution_attachment(*, evolution: Evolution, document, actor) -> None:
    profile = getattr(evolution, "clinical_data", None)
    if evolution.created_by_id != actor.id:
        raise PermissionDenied("Somente o autor pode remover anexos.")
    if not evolution.can_be_edited():
        raise ValidationError("Este anexo não pode mais ser removido.")
    if profile and profile.status != EvolutionClinicalData.Status.DRAFT:
        raise ValidationError("Anexos de uma evolução finalizada não podem ser removidos.")
    document.soft_delete()
