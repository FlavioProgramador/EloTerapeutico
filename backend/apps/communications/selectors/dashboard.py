from __future__ import annotations

from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone

from apps.communications.models import Communication
from apps.organizations.models import OrganizationMembership


def communication_dashboard(user, start_date=None, end_date=None, *, organization=None):
    end = end_date or timezone.now()
    start = start_date or end - timedelta(days=30)
    queryset = Communication.objects.filter(
        created_at__gte=start,
        created_at__lte=end,
    )
    if organization is not None:
        membership = OrganizationMembership.objects.filter(
            user=user,
            organization=organization,
            status=OrganizationMembership.Status.ACTIVE,
        ).first()
        if membership is None:
            queryset = queryset.none()
        else:
            queryset = queryset.filter(organization=organization)
            if membership.role == OrganizationMembership.Role.THERAPIST:
                queryset = queryset.filter(owner=user)
    else:
        queryset = queryset.filter(owner=user)

    by_status = list(
        queryset.values("status").annotate(total=Count("id")).order_by("status")
    )
    status_counts = {item["status"]: item["total"] for item in by_status}
    total = sum(status_counts.values())

    delivered = (
        status_counts.get(Communication.Status.DELIVERED, 0)
        + status_counts.get(Communication.Status.READ, 0)
        + status_counts.get(Communication.Status.RESPONDED, 0)
    )
    sent_like = status_counts.get(Communication.Status.SENT, 0) + delivered

    by_channel = list(
        queryset.values("channel").annotate(total=Count("id")).order_by("channel")
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
            "scheduled": status_counts.get(Communication.Status.SCHEDULED, 0),
            "delivered": delivered,
            "failed": status_counts.get(Communication.Status.FAILED, 0),
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
