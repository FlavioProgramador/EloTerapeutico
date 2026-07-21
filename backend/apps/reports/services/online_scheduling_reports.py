"""Relatório de agendamento online enquanto o recurso permanece desativado."""

from typing import Any

from apps.reports.services.periods import resolve_period
from apps.reports.services.tenant import resolve_report_organization


def online_scheduling_report(user, params, organization=None) -> dict[str, Any]:
    start, end = resolve_period(params)
    resolve_report_organization(user=user, organization=organization)
    return {
        "period": {"start_date": start.isoformat(), "end_date": end.isoformat()},
        "enabled": False,
        "kpis": {
            "views": 0,
            "unique_views": 0,
            "requests": 0,
            "pending_requests": 0,
            "conversion_rate": 0,
            "average_approval_minutes": 0,
        },
        "statuses": {
            "approved": {"count": 0, "percentage": 0},
            "pending": {"count": 0, "percentage": 0},
            "rejected": {"count": 0, "percentage": 0},
        },
    }
