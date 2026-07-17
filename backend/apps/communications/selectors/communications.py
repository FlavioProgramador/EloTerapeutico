from __future__ import annotations

from apps.communications.models import Communication


def communications_for_user(user):
    return (
        Communication.objects.filter(owner=user, archived_at__isnull=True)
        .select_related("patient", "appointment", "template", "created_by")
        .prefetch_related("recipients", "attempts")
    )
