"""Compatibilidade para models usados pela camada HTTP."""

from apps.scheduling.models import (
    Appointment,
    AppointmentRecurrence,
    PatientPackage,
    ScheduleBlock,
)

__all__ = [
    "Appointment",
    "AppointmentRecurrence",
    "PatientPackage",
    "ScheduleBlock",
]
