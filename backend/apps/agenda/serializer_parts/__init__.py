from .appointment_read import AppointmentDetailSerializer, AppointmentListSerializer
from .appointment_write import (
    AppointmentCreateSerializer,
    AppointmentStatusUpdateSerializer,
    AppointmentUpdateSerializer,
)
from .availability import CheckAvailabilitySerializer, ScheduleBlockSerializer
from .packages import PatientPackageSerializer
from .recurrences import AppointmentRecurrenceSerializer
from .summary import (
    AppointmentReminderSerializer,
    PackageSessionSerializer,
    RoomSerializer,
    TelemedicineRoomSerializer,
)

__all__ = [name for name in globals() if name.endswith("Serializer")]
