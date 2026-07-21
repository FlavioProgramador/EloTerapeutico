from __future__ import annotations

from django.db.models import Q

from apps.communications.models import CommunicationTemplate
from apps.organizations.models import OrganizationMembership


def templates_for_user(user, *, organization=None):
    queryset = CommunicationTemplate.objects.filter(is_archived=False)
    if not user or user.is_anonymous:
        return queryset.none()
    if organization is None:
        organization_ids = OrganizationMembership.objects.filter(
            user=user,
            status=OrganizationMembership.Status.ACTIVE,
        ).values_list("organization_id", flat=True)
        return queryset.filter(
            Q(
                organization_id__in=organization_ids,
                is_system_template=False,
            )
            | Q(
                organization__isnull=True,
                owner__isnull=True,
                is_system_template=True,
            )
        ).order_by("name")
    if not OrganizationMembership.objects.filter(
        user=user,
        organization=organization,
        status=OrganizationMembership.Status.ACTIVE,
    ).exists():
        return queryset.none()
    return queryset.filter(
        Q(organization=organization, is_system_template=False)
        | Q(
            organization__isnull=True,
            owner__isnull=True,
            is_system_template=True,
        )
    ).order_by("name")
