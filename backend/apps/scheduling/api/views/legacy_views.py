"""Views públicas da agenda."""

from apps.scheduling.api.views.appointments import AppointmentViewSet
from apps.scheduling.api.views.operations import (
    PackageSessionViewSet,
    PatientPackageViewSet,
    RoomViewSet,
    ScheduleBlockViewSet,
)
from apps.scheduling.api.views.recurrences import AppointmentRecurrenceViewSet
from apps.scheduling.api.views.telemedicine import (
    AppointmentReminderViewSet,
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
