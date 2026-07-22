from __future__ import annotations

from datetime import timedelta

from django.db.models import Count, QuerySet
from django.utils import timezone

from apps.scheduling.models import (
    TelemedicineInvitation,
    TelemedicineParticipantSession,
    TelemedicineRoom,
    TelemedicineWebhookEvent,
)

METRICS_WINDOW_HOURS = 24


def get_telemedicine_operational_metrics(
    rooms: QuerySet[TelemedicineRoom],
) -> dict[str, object]:
    """Retorna métricas agregadas do escopo recebido, sem identificadores pessoais."""

    now = timezone.now()
    since = now - timedelta(hours=METRICS_WINDOW_HOURS)
    room_ids = rooms.order_by().values("pk")
    status_rows = rooms.order_by().values("status").annotate(total=Count("pk"))

    participant_sessions = TelemedicineParticipantSession.objects.filter(
        room_id__in=room_ids
    )
    invitations = TelemedicineInvitation.objects.filter(room_id__in=room_ids)
    webhook_events = TelemedicineWebhookEvent.objects.filter(room_id__in=room_ids)

    return {
        "generated_at": now,
        "window_hours": METRICS_WINDOW_HOURS,
        "rooms": {
            "total": rooms.count(),
            "by_status": {
                row["status"]: row["total"]
                for row in status_rows
            },
            "failed": rooms.filter(status=TelemedicineRoom.Status.FAILED).count(),
        },
        "participants": {
            "active": participant_sessions.filter(left_at__isnull=True).count(),
            "joined_in_window": participant_sessions.filter(
                joined_at__gte=since
            ).count(),
            "aborted_in_window": participant_sessions.filter(
                joined_at__gte=since,
                connection_aborted=True,
            ).count(),
        },
        "invitations": {
            "created_in_window": invitations.filter(created_at__gte=since).count(),
            "used_in_window": invitations.filter(last_used_at__gte=since).count(),
            "active": invitations.filter(
                revoked_at__isnull=True,
                expires_at__gt=now,
            ).count(),
        },
        "webhooks": {
            "received_in_window": webhook_events.filter(
                received_at__gte=since
            ).count(),
            "processing_errors_in_window": webhook_events.filter(
                received_at__gte=since,
            ).exclude(processing_error="").count(),
        },
    }
