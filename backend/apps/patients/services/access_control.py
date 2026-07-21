"""Regras centralizadas de acesso a pacientes dentro do tenant ativo."""

from django.db.models import Q

from apps.organizations.models import OrganizationMembership

FULL_TENANT_PATIENT_ROLES = {
    OrganizationMembership.Role.OWNER,
    OrganizationMembership.Role.ADMIN,
    OrganizationMembership.Role.RECEPTIONIST,
    OrganizationMembership.Role.FINANCE,
    OrganizationMembership.Role.VIEWER,
}


def patient_access_q(user, *, membership=None) -> Q:
    """Restringe pacientes pela membership e pelo vínculo clínico do profissional."""

    if not user or not getattr(user, "is_authenticated", False) or membership is None:
        return Q(pk__in=[])
    if membership.user_id != user.pk or membership.status != OrganizationMembership.Status.ACTIVE:
        return Q(pk__in=[])
    if membership.role in FULL_TENANT_PATIENT_ROLES:
        return Q()
    if membership.role == OrganizationMembership.Role.THERAPIST:
        return Q(therapist=user) | Q(
            professional_links__professional=user,
            professional_links__is_active=True,
        )
    return Q(pk__in=[])


def can_access_patient(user, patient, *, membership=None, allow_secretary: bool = False) -> bool:
    """Valida tenant, membership ativa e vínculo mínimo necessário."""

    if not user or not getattr(user, "is_authenticated", False) or membership is None:
        return False
    if membership.user_id != user.pk or membership.organization_id != patient.organization_id:
        return False
    if membership.status != OrganizationMembership.Status.ACTIVE:
        return False
    if membership.role in {
        OrganizationMembership.Role.OWNER,
        OrganizationMembership.Role.ADMIN,
        OrganizationMembership.Role.FINANCE,
        OrganizationMembership.Role.VIEWER,
    }:
        return True
    if membership.role == OrganizationMembership.Role.RECEPTIONIST:
        return allow_secretary
    if membership.role == OrganizationMembership.Role.THERAPIST:
        if patient.therapist_id == user.id:
            return True
        return patient.professional_links.filter(
            professional_id=user.id,
            is_active=True,
        ).exists()
    return False


def can_manage_patient(user, patient, *, membership=None) -> bool:
    """Autoriza alteração apenas no mesmo tenant e para papéis com escrita."""

    if not can_access_patient(
        user,
        patient,
        membership=membership,
        allow_secretary=True,
    ):
        return False
    if membership.role in {
        OrganizationMembership.Role.OWNER,
        OrganizationMembership.Role.ADMIN,
    }:
        return True
    return (
        membership.role == OrganizationMembership.Role.THERAPIST
        and patient.therapist_id == user.id
    )
