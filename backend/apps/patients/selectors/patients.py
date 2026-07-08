"""Consultas reutilizáveis do domínio de pacientes."""

from apps.patients.services.access_control import patient_access_q

from ..models import Patient


def patients_accessible_to(user, *, include_deleted: bool = False):
    manager = Patient.all_objects if include_deleted else Patient.objects
    queryset = manager.select_related("therapist")
    if not user or user.is_anonymous:
        return queryset.none()
    return queryset.filter(patient_access_q(user)).distinct()
