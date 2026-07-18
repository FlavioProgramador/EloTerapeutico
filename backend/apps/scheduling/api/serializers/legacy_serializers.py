"""Serializers públicos da agenda."""

from apps.scheduling.api.serializers import (
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
