from __future__ import annotations

from apps.communications.models import CommunicationAutomation


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
