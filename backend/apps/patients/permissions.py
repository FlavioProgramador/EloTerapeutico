"""Regras centralizadas de acesso a pacientes e seus dados clínicos."""

from django.db.models import Q


def patient_access_q(user) -> Q:
    """Filtro reutilizável para restringir pacientes aos profissionais vinculados."""

    if user.is_admin_role or user.is_secretary:
        return Q()
    return Q(therapist=user) | Q(
        professional_links__professional=user,
        professional_links__is_active=True,
    )


def can_access_patient(user, patient, *, allow_secretary: bool = False) -> bool:
    """Valida vínculo administrativo ou clínico sem confiar apenas no ID da URL."""

    if not user or not user.is_authenticated:
        return False
    if user.is_admin_role:
        return True
    if user.is_secretary:
        return allow_secretary
    if patient.therapist_id == user.id:
        return True
    return patient.professional_links.filter(
        professional_id=user.id,
        is_active=True,
    ).exists()


def can_manage_patient(user, patient) -> bool:
    """Apenas administrador ou terapeuta principal altera dados sensíveis."""

    if not user or not user.is_authenticated:
        return False
    return user.is_admin_role or patient.therapist_id == user.id
