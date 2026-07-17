from __future__ import annotations

from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import Communication, CommunicationAutomation, CommunicationTemplate, InAppNotification


def communications_for_user(user):
    return (
        Communication.objects.filter(owner=user, archived_at__isnull=True)
        .select_related("patient", "appointment", "template", "created_by")
        .prefetch_related("recipients", "attempts")
    )


def templates_for_user(user):
    return CommunicationTemplate.objects.filter(
        Q(owner=user) | Q(owner__isnull=True, is_system_template=True),
        is_archived=False,
    ).order_by("name")


def active_automations_for_event(user, event_type: str):
    return (
        CommunicationAutomation.objects.filter(owner=user, event_type=event_type, is_active=True)
        .select_related("template")
        .order_by("id")
    )


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


def communication_dashboard(user, start_date=None, end_date=None):
    end = end_date or timezone.now()
    start = start_date or end - timedelta(days=30)
    queryset = Communication.objects.filter(owner=user, created_at__gte=start, created_at__lte=end)
    total = queryset.count()
    sent_like = queryset.filter(
        status__in=[
            Communication.Status.SENT,
            Communication.Status.DELIVERED,
            Communication.Status.READ,
            Communication.Status.RESPONDED,
        ]
    ).count()
    by_channel = list(queryset.values("channel").annotate(total=Count("id")).order_by("channel"))
    by_status = list(queryset.values("status").annotate(total=Count("id")).order_by("status"))
    daily = list(
        queryset.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Count("id"))
        .order_by("day")
    )
    return {
        "period": {"start": start, "end": end},
        "metrics": {
            "total": total,
            "scheduled": queryset.filter(status=Communication.Status.SCHEDULED).count(),
            "delivered": queryset.filter(
                status__in=[Communication.Status.DELIVERED, Communication.Status.READ, Communication.Status.RESPONDED]
            ).count(),
            "failed": queryset.filter(status=Communication.Status.FAILED).count(),
            "appointment_confirmations": queryset.filter(
                category=Communication.Category.APPOINTMENT_CONFIRMATION,
                status__in=[Communication.Status.DELIVERED, Communication.Status.READ, Communication.Status.RESPONDED],
            ).count(),
            "success_rate": round((sent_like / total) * 100, 2) if total else 0,
        },
        "by_channel": by_channel,
        "by_status": by_status,
        "daily": daily,
    }
