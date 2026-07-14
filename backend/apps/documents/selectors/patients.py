"""Consultas de pacientes usadas pelo domínio documental."""

from __future__ import annotations

from apps.patients.models import Patient


def get_accessible_patient(*, owner, patient_id: int) -> Patient | None:
    return Patient.objects.filter(
        pk=patient_id,
        therapist=owner,
        deleted_at__isnull=True,
    ).first()
