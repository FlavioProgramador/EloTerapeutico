from __future__ import annotations

from apps.communications.models import CommunicationAutomation


def active_automations_for_event(user, event_type: str):
    return (
        CommunicationAutomation.objects.filter(
            owner=user,
            event_type=event_type,
            is_active=True,
        )
        .select_related("template")
        .order_by("id")
    )
