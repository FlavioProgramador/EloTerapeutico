"""Serializers de escrita e transição de consultas."""

from apps.scheduling.api.serializers import (
    AppointmentCreateSerializer,
    AppointmentStatusUpdateSerializer,
)
from apps.scheduling.api.serializers.appointment_write import AppointmentUpdateSerializer

__all__ = [
    "AppointmentCreateSerializer",
    "AppointmentStatusUpdateSerializer",
    "AppointmentUpdateSerializer",
]
