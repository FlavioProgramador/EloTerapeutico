"""Selectors de usuários relevantes para scheduling."""

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from apps.organizations.models import OrganizationMembership


def get_accessible_therapist(*, actor, therapist_id=None, organization=None):
    """Resolve o profissional respeitando o papel do ator e a organização."""

    if actor.is_therapist or not therapist_id:
        return actor
    if actor.is_admin_role or actor.is_secretary:
        queryset = get_user_model().objects.filter(role="therapist")
        if organization is not None:
            therapist_ids = OrganizationMembership.objects.filter(
                organization=organization,
                status=OrganizationMembership.Status.ACTIVE,
            ).values_list("user_id", flat=True)
            queryset = queryset.filter(pk__in=therapist_ids)
        return get_object_or_404(
            queryset,
            pk=therapist_id,
        )
    return actor


__all__ = ["get_accessible_therapist"]
