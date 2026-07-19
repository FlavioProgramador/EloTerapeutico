"""Compatibilidade para selectors movidos para ``apps.scheduling``."""

from apps.scheduling.selectors import (
    AppointmentConflictResult,
    appointment_queryset,
    available_slots,
    get_appointment_conflicts,
)

__all__ = [
    "AppointmentConflictResult",
    "appointment_queryset",
    "available_slots",
    "get_appointment_conflicts",
]
