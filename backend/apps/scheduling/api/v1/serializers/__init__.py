"""Contratos públicos de serializers da API v1 de scheduling."""

from .appointment_read import AppointmentDetailSerializer, AppointmentListSerializer
from .appointment_write import (
    AppointmentCreateSerializer,
    AppointmentStatusUpdateSerializer,
    AppointmentUpdateSerializer,
)
from .availability import CheckAvailabilitySerializer
from .package_sessions import PackageSessionSerializer
from .packages import PatientPackageSerializer
from .recurrences import AppointmentRecurrenceSerializer
from .reminders import AppointmentReminderSerializer
from .rooms import RoomSerializer
from .schedule_blocks import ScheduleBlockSerializer
from .telemedicine import (
    TelemedicineConsentSerializer,
    TelemedicineInvitationSendSerializer,
    TelemedicineInvitationTokenSerializer,
    TelemedicineParticipantRemovalSerializer,
    TelemedicinePublicLeaveSerializer,
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
    "TelemedicineConsentSerializer",
    "TelemedicineInvitationSendSerializer",
    "TelemedicineInvitationTokenSerializer",
    "TelemedicineParticipantRemovalSerializer",
    "TelemedicinePublicLeaveSerializer",
    "TelemedicineRoomSerializer",
]
