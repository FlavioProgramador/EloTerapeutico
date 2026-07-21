from __future__ import annotations

from apps.communications.models import Communication
from apps.organizations.models import OrganizationMembership


def communications_for_user(user, *, organization=None):
    queryset = (
        Communication.objects.filter(archived_at__isnull=True)
        .select_related(
            "organization",
            "patient",
            "appointment",
            "template",
            "created_by",
        )
        .prefetch_related("recipients", "attempts")
    )
    if not user or user.is_anonymous:
        return queryset.none()

    membership = None
    if organization is None:
        organization_ids = OrganizationMembership.objects.filter(
            user=user,
            status=OrganizationMembership.Status.ACTIVE,
        ).values_list("organization_id", flat=True)
        return queryset.filter(organization_id__in=organization_ids)

    membership = OrganizationMembership.objects.filter(
        user=user,
        organization=organization,
        status=OrganizationMembership.Status.ACTIVE,
    ).first()
    if membership is None:
        return queryset.none()
    queryset = queryset.filter(organization=organization)
    if membership.role == OrganizationMembership.Role.THERAPIST:
        return queryset.filter(owner=user)
    return queryset
