"""Compatibilidade para serializers da API v1 de scheduling."""

from apps.scheduling.api.v1.serializers import (
    AppointmentCreateSerializer,
    AppointmentDetailSerializer,
    AppointmentListSerializer,
    AppointmentRecurrenceSerializer,
    AppointmentReminderSerializer,
    AppointmentStatusUpdateSerializer,
    AppointmentUpdateSerializer,
    CheckAvailabilitySerializer,
    PackageSessionSerializer,
    PatientPackageSerializer,
    RoomSerializer,
    ScheduleBlockSerializer,
    TelemedicineRoomSerializer,
)

__all__ = [
    "AppointmentCreateSerializer",
    "AppointmentDetailSerializer",
    "AppointmentListSerializer",
    "AppointmentRecurrenceSerializer",
    "AppointmentReminderSerializer",
    "AppointmentStatusUpdateSerializer",
    "AppointmentUpdateSerializer",
    "CheckAvailabilitySerializer",
    "PackageSessionSerializer",
    "PatientPackageSerializer",
    "RoomSerializer",
    "ScheduleBlockSerializer",
    "TelemedicineRoomSerializer",
]
