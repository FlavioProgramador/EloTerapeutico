"""Métricas agregadas do painel de pacientes."""

from datetime import timedelta

from django.utils import timezone


def patient_metrics(queryset) -> dict:
    today = timezone.localdate()
    current_month = today.replace(day=1)
    previous_month_end = current_month - timedelta(days=1)
    previous_month = previous_month_end.replace(day=1)
    total = queryset.count()
    active = queryset.filter(status="active").count()
    discharged = queryset.filter(status__in=["discharged", "inactive"]).count()
    return {
        "total": total,
        "active": active,
        "active_percentage": round(active / total * 100) if total else 0,
        "discharged": discharged,
        "discharged_percentage": round(discharged / total * 100) if total else 0,
        "new_current_month": queryset.filter(
            created_at__date__gte=current_month
        ).count(),
        "new_previous_month": queryset.filter(
            created_at__date__gte=previous_month,
            created_at__date__lte=previous_month_end,
        ).count(),
    }
