"""Relatório de agendamento online enquanto o recurso permanece desativado."""

from typing import Any

from apps.reports.services.periods import resolve_period


def online_scheduling_report(user, params) -> dict[str, Any]:
    start, end = resolve_period(params)
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
