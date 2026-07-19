"""Compatibilidade para serializers resumidos."""

from apps.scheduling.api.serializers.summary import (
    AppointmentReminderSerializer,
    PackageSessionSerializer,
    PatientSummarySerializer,
    RoomSerializer,
    TelemedicineRoomSerializer,
    TherapistSummarySerializer,
)

__all__ = [
    "AppointmentReminderSerializer",
    "PackageSessionSerializer",
    "PatientSummarySerializer",
    "RoomSerializer",
    "TelemedicineRoomSerializer",
    "TherapistSummarySerializer",
]
