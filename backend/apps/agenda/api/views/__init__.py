"""Compatibilidade para os ViewSets públicos de scheduling."""

from apps.scheduling.api.v1.views import (
    AppointmentRecurrenceViewSet,
    AppointmentReminderViewSet,
    AppointmentViewSet,
    PackageSessionViewSet,
    PatientPackageViewSet,
    RoomViewSet,
    ScheduleBlockViewSet,
    TelemedicineAccessView,
    TelemedicineRoomViewSet,
)

__all__ = [
    "AppointmentRecurrenceViewSet",
    "AppointmentReminderViewSet",
    "AppointmentViewSet",
    "PackageSessionViewSet",
    "PatientPackageViewSet",
    "RoomViewSet",
    "ScheduleBlockViewSet",
    "TelemedicineAccessView",
    "TelemedicineRoomViewSet",
]
