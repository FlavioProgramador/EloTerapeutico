"""Compatibilidade para o model de consultas."""

from apps.scheduling.models.appointments import ACTIVE_APPOINTMENT_STATUSES, Appointment

__all__ = ["ACTIVE_APPOINTMENT_STATUSES", "Appointment"]
