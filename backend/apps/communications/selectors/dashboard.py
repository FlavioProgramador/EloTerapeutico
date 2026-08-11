from __future__ import annotations

from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.communications.models import Communication


def communication_dashboard(user, start_date=None, end_date=None, *, organization=None):
    end = end_date or timezone.now()
    start = start_date or end - timedelta(days=30)
    queryset = Communication.objects.filter(
        created_at__gte=start,
        created_at__lte=end,
    )
    if organization is not None:
        queryset = queryset.filter(organization=organization)
    else:
        queryset = queryset.filter(owner=user)
    total = queryset.count()
    sent_like = queryset.filter(
        status__in=[
            Communication.Status.SENT,
            Communication.Status.DELIVERED,
            Communication.Status.READ,
            Communication.Status.RESPONDED,
        ]
    ).count()
    by_channel = list(
        queryset.values("channel").annotate(total=Count("id")).order_by("channel")
    )
    by_status = list(
        queryset.values("status").annotate(total=Count("id")).order_by("status")
    )
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
            "scheduled": queryset.filter(
                status=Communication.Status.SCHEDULED
            ).count(),
            "delivered": queryset.filter(
                status__in=[
                    Communication.Status.DELIVERED,
                    Communication.Status.READ,
                    Communication.Status.RESPONDED,
                ]
            ).count(),
            "failed": queryset.filter(status=Communication.Status.FAILED).count(),
            "appointment_confirmations": queryset.filter(
                category=Communication.Category.APPOINTMENT_CONFIRMATION,
                status__in=[
                    Communication.Status.DELIVERED,
                    Communication.Status.READ,
                    Communication.Status.RESPONDED,
                ],
            ).count(),
            "success_rate": round((sent_like / total) * 100, 2) if total else 0,
        },
        "by_channel": by_channel,
        "by_status": by_status,
        "daily": daily,
    }
