from __future__ import annotations

from apps.communications.models import CommunicationAutomation
from apps.organizations.models import OrganizationMembership


def automations_for_user(user, *, organization=None):
    queryset = (
        CommunicationAutomation.objects.all()
        .select_related("organization", "template", "owner")
        .prefetch_related("runs")
    )
    if not user or user.is_anonymous:
        return queryset.none()

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


def active_automations_for_event(user, event_type: str, *, organization=None):
    queryset = CommunicationAutomation.objects.filter(
        event_type=event_type,
        is_active=True,
    )
    if organization is not None:
        queryset = queryset.filter(organization=organization)
    else:
        queryset = queryset.filter(owner=user)
    return queryset.select_related(
        "organization",
        "template",
        "owner",
        "created_by",
    ).order_by("id")
