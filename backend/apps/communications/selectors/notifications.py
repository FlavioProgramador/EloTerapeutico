from __future__ import annotations

from django.db.models import Q
from django.utils import timezone

from apps.communications.models import InAppNotification


def unread_notifications(user):
    now = timezone.now()
    return (
        InAppNotification.objects.filter(
            recipient=user,
            is_read=False,
            archived_at__isnull=True,
        )
        .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
        .order_by("-created_at")
    )
