"""Contratos públicos de views da API v1 de scheduling."""

from .appointments import AppointmentViewSet
from .package_sessions import PackageSessionViewSet
from .packages import PatientPackageViewSet
from .recurrences import AppointmentRecurrenceViewSet
from .reminders import AppointmentReminderViewSet
from .rooms import RoomViewSet
from .schedule_blocks import ScheduleBlockViewSet
from .telemedicine import TelemedicineAccessView, TelemedicineRoomViewSet

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
