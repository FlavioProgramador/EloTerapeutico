"""Compatibilidade para services de consultas."""

from apps.scheduling.services.appointments import (
    cancel_appointment_for_deletion,
    create_appointment,
    update_appointment,
    update_appointment_status,
)

__all__ = [
    "cancel_appointment_for_deletion",
    "create_appointment",
    "update_appointment",
    "update_appointment_status",
]
