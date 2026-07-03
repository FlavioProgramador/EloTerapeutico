"""Consultas autorizadas e otimizadas para evoluções clínicas."""

from __future__ import annotations

from django.db.models import Q

from apps.agenda.models import Appointment

from ..models import Evolution


def evolutions_for_patient(*, patient, user, status: str | None = None):
    queryset = (
        Evolution.objects.filter(patient=patient)
        .select_related(
            "created_by",
            "clinical_data",
            "appointment",
            "appointment__therapist",
            "appointment__patient",
        )
        .prefetch_related("versions", "documents")
        .order_by("-session_date", "-created_at")
    )
    if not user.has_perm("records.view_confidential_evolution"):
        queryset = queryset.filter(Q(is_confidential=False) | Q(created_by=user))
    if status:
        queryset = queryset.filter(clinical_data__status=status)
    return queryset


def available_appointments_for_evolution(
    *,
    patient,
    include_cancelled: bool = False,
    limit: int = 100,
):
    queryset = (
        Appointment.objects.filter(patient=patient, evolution__isnull=True)
        .select_related("patient", "therapist")
        .order_by("-start_time")
    )
    if not include_cancelled:
        queryset = queryset.exclude(status=Appointment.Status.CANCELLED)
    return queryset[:limit]


def active_evolution_attachments(*, evolution):
    return evolution.documents.filter(
        deleted_at__isnull=True,
        is_archived=False,
    ).order_by("created_at")
