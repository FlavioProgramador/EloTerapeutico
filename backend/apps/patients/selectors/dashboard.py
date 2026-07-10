"""Métricas agregadas do painel de pacientes."""

from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone


def patient_metrics(queryset) -> dict:
    today = timezone.localdate()
    current_month = today.replace(day=1)
    previous_month_end = current_month - timedelta(days=1)
    previous_month = previous_month_end.replace(day=1)

    metrics = queryset.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(status="active")),
        discharged=Count("id", filter=Q(status__in=["discharged", "inactive"])),
        new_current_month=Count("id", filter=Q(created_at__date__gte=current_month)),
        new_previous_month=Count(
            "id",
            filter=Q(
                created_at__date__gte=previous_month,
                created_at__date__lte=previous_month_end,
            ),
        ),
    )

    total = metrics["total"]
    active = metrics["active"]
    discharged = metrics["discharged"]

    return {
        "total": total,
        "active": active,
        "active_percentage": round(active / total * 100) if total else 0,
        "discharged": discharged,
        "discharged_percentage": round(discharged / total * 100) if total else 0,
        "new_current_month": metrics["new_current_month"],
        "new_previous_month": metrics["new_previous_month"],
    }
