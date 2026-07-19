"""Compatibilidade para views operacionais de scheduling."""

from apps.scheduling.api.views.operations import (
    PackageSessionViewSet,
    PatientPackageViewSet,
    RoomViewSet,
    ScheduleBlockViewSet,
)

__all__ = [
    "PackageSessionViewSet",
    "PatientPackageViewSet",
    "RoomViewSet",
    "ScheduleBlockViewSet",
]
