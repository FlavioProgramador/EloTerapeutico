"""Contratos públicos de views da API v1 de scheduling."""

from .appointments import AppointmentViewSet
from .package_sessions import PackageSessionViewSet
from .packages import PatientPackageViewSet
from .recurrences import AppointmentRecurrenceViewSet
from .reminders import AppointmentReminderViewSet
from .rooms import RoomViewSet
from .schedule_blocks import ScheduleBlockViewSet
from .telemedicine import (
    LiveKitWebhookView,
    TelemedicineAccessView,
    TelemedicinePublicConsentView,
    TelemedicinePublicExchangeView,
    TelemedicinePublicJoinView,
    TelemedicinePublicLeaveView,
    TelemedicineRoomViewSet,
)

__all__ = [
    "AppointmentRecurrenceViewSet",
    "AppointmentReminderViewSet",
    "AppointmentViewSet",
    "LiveKitWebhookView",
    "PackageSessionViewSet",
    "PatientPackageViewSet",
    "RoomViewSet",
    "ScheduleBlockViewSet",
    "TelemedicineAccessView",
    "TelemedicinePublicConsentView",
    "TelemedicinePublicExchangeView",
    "TelemedicinePublicJoinView",
    "TelemedicinePublicLeaveView",
    "TelemedicineRoomViewSet",
]
