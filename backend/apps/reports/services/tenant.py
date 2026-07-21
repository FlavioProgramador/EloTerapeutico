"""Resolução segura do tenant para builders de relatórios."""

from rest_framework.exceptions import PermissionDenied

from apps.organizations.models import OrganizationMembership


def resolve_report_organization(*, user, organization=None):
    memberships = OrganizationMembership.objects.filter(
        user=user,
        status=OrganizationMembership.Status.ACTIVE,
    ).select_related("organization")
    if organization is not None:
        membership = memberships.filter(organization=organization).first()
        if membership is None:
            raise PermissionDenied("A organização selecionada não está disponível.")
        return membership.organization

    membership = memberships.filter(is_default=True).first()
    if membership is None:
        first_two = list(memberships[:2])
        membership = first_two[0] if len(first_two) == 1 else None
    if membership is None:
        raise PermissionDenied("Selecione uma organização para consultar relatórios.")
    return membership.organization


__all__ = ["resolve_report_organization"]
