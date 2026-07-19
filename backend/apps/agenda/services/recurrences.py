"""Compatibilidade para services de recorrências."""

from apps.scheduling.services.recurrences import (
    apply_bulk_recurrence_change,
    end_recurrence,
    generate_recurrence_appointments,
    recurrence_dates,
    set_recurrence_status,
)

__all__ = [
    "apply_bulk_recurrence_change",
    "end_recurrence",
    "generate_recurrence_appointments",
    "recurrence_dates",
    "set_recurrence_status",
]
