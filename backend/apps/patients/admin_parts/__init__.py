"""Componentes do admin de pacientes."""

from .filters import IsMinorFilter, SoftDeletedFilter
from .inlines import AppointmentInline, FinancialTransactionInline
from .mixins import PatientAdminActionsMixin, PatientAdminDisplayMixin

__all__ = [
    "AppointmentInline",
    "FinancialTransactionInline",
    "IsMinorFilter",
    "PatientAdminActionsMixin",
    "PatientAdminDisplayMixin",
    "SoftDeletedFilter",
]
