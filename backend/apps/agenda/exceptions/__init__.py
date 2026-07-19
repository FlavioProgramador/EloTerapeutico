"""Compatibilidade para exceções movidas para scheduling."""

from apps.scheduling.exceptions import (
    AgendaDomainError,
    CompletedAppointmentDeletionError,
    CompletedPackageSessionRemovalError,
    InvalidRecurrenceScopeError,
    RecurrenceConflictError,
    SchedulingDomainError,
    TelemedicineUnavailableError,
)

__all__ = [
    "AgendaDomainError",
    "CompletedAppointmentDeletionError",
    "CompletedPackageSessionRemovalError",
    "InvalidRecurrenceScopeError",
    "RecurrenceConflictError",
    "SchedulingDomainError",
    "TelemedicineUnavailableError",
]
