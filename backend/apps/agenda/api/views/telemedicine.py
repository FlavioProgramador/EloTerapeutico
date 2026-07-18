"""Compatibilidade para views de telemedicina e lembretes."""

from apps.scheduling.api.views.telemedicine import (
    AppointmentReminderViewSet,
    TelemedicineAccessView,
    TelemedicineRoomViewSet,
)

__all__ = [
    "AppointmentReminderViewSet",
    "TelemedicineAccessView",
    "TelemedicineRoomViewSet",
]
