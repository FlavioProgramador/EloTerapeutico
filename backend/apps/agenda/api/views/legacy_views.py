"""Views públicas da agenda."""

from apps.agenda.api.views.appointments import AppointmentViewSet
from apps.agenda.api.views.operations import (
    PackageSessionViewSet,
    PatientPackageViewSet,
    RoomViewSet,
    ScheduleBlockViewSet,
)
from apps.agenda.api.views.recurrences import AppointmentRecurrenceViewSet
from apps.agenda.api.views.telemedicine import (
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
