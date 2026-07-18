"""Fachada de compatibilidade para os models de ``apps.scheduling``."""

from apps.scheduling.models import (
    Appointment,
    AppointmentRecurrence,
    AppointmentReminder,
    PackageSession,
    PatientPackage,
    Room,
    ScheduleBlock,
    TelemedicineRoom,
)

__all__ = [
    "Appointment",
    "AppointmentRecurrence",
    "AppointmentReminder",
    "PackageSession",
    "PatientPackage",
    "Room",
    "ScheduleBlock",
    "TelemedicineRoom",
]
