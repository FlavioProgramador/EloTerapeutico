from .appointments import AppointmentViewSet
from .operations import (
    PackageSessionViewSet,
    PatientPackageViewSet,
    RoomViewSet,
    ScheduleBlockViewSet,
)
from .recurrences import AppointmentRecurrenceViewSet
from .telemedicine import (
    AppointmentReminderViewSet,
    TelemedicineAccessView,
    TelemedicineRoomViewSet,
)

__all__ = [
    name
    for name in globals()
    if name.endswith("ViewSet") or name.endswith("View")
]
