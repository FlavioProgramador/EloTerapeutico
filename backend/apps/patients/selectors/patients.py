"""Consultas reutilizáveis do domínio de pacientes."""

from apps.patients.services.access_control import patient_access_q

from ..models import Patient


def patients_accessible_to(
    user,
    *,
    organization,
    membership,
    include_deleted: bool = False,
):
    """Lista somente pacientes do tenant ativo permitidos à membership."""

    manager = Patient.all_objects if include_deleted else Patient.objects
    queryset = manager.select_related("organization", "therapist")
    if not user or user.is_anonymous or organization is None or membership is None:
        return queryset.none()
    return (
        queryset.filter(organization=organization)
        .filter(patient_access_q(user, membership=membership))
        .distinct()
    )
