"""Consultas de pacientes usadas pelo domínio documental."""

from __future__ import annotations

from apps.organizations.models import OrganizationMembership
from apps.organizations.services.tenant_context import list_active_memberships_for_user
from apps.patients.models import Patient
from apps.patients.services.access_control import patient_access_q


def get_accessible_patient(
    *,
    owner,
    patient_id: int,
    organization=None,
) -> Patient | None:
    membership = None
    if organization is None and owner and getattr(owner, "is_authenticated", False):
        memberships = list_active_memberships_for_user(user=owner)
        default_membership = memberships.filter(is_default=True).first()
        if default_membership is not None:
            membership = default_membership
            organization = default_membership.organization
        elif memberships.count() == 1:
            first_membership = memberships.first()
            if first_membership is not None:
                membership = first_membership
                organization = first_membership.organization

    if organization is not None and membership is None and owner:
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
