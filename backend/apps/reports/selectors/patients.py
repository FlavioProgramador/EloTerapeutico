"""Selectors de pacientes para relatórios."""

from django.db.models import QuerySet

from apps.organizations.models import OrganizationMembership
from apps.patients.models import Patient


def patients_for_user(*, user, organization) -> QuerySet[Patient]:
    membership = OrganizationMembership.objects.filter(
        organization=organization,
        user=user,
        status=OrganizationMembership.Status.ACTIVE,
    ).first()
    queryset = Patient.objects.filter(
        organization=organization,
        deleted_at__isnull=True,
    ).select_related("therapist")
    if membership is None:
        return queryset.none()
    if membership.role == OrganizationMembership.Role.THERAPIST:
        return queryset.filter(therapist=user)
    return queryset


def patients_for_owner(*, owner) -> QuerySet[Patient]:
    """Fachada legada restrita à carteira direta do profissional."""

    return Patient.objects.filter(therapist=owner).select_related("therapist")
