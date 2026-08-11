"""Consultas de pacientes usadas pelo domínio documental."""

from __future__ import annotations

from apps.organizations.models import OrganizationMembership
from apps.patients.models import Patient
from apps.patients.services.access_control import patient_access_q


def get_accessible_patient(
    *,
    owner,
    patient_id: int,
    organization=None,
) -> Patient | None:
    membership = None
    if organization is not None:
        membership = OrganizationMembership.objects.filter(
            organization=organization,
            user=owner,
            status=OrganizationMembership.Status.ACTIVE,
        ).first()
    queryset = Patient.objects.filter(
        pk=patient_id,
        deleted_at__isnull=True,
    )
    if organization is not None:
        queryset = queryset.filter(organization=organization)
    return queryset.filter(
        patient_access_q(owner, membership=membership)
    ).distinct().first()
