"""Serializers de leitura de consultas."""

from apps.scheduling.api.serializers.appointment_read import (
    AppointmentDetailSerializer,
    AppointmentListSerializer,
)

__all__ = ["AppointmentDetailSerializer", "AppointmentListSerializer"]
