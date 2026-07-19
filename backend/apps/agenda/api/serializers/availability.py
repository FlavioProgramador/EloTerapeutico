"""Compatibilidade para serializers de disponibilidade."""

from apps.scheduling.api.v1.serializers import (
    CheckAvailabilitySerializer,
    ScheduleBlockSerializer,
)

__all__ = ["CheckAvailabilitySerializer", "ScheduleBlockSerializer"]
