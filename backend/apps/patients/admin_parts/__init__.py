"""Componentes do admin de pacientes."""

from .filters import IsMinorFilter, SoftDeletedFilter
from .inlines import AppointmentInline, EvolutionInline, FinancialTransactionInline
from .mixins import PatientAdminActionsMixin, PatientAdminDisplayMixin

__all__ = [
    "AppointmentInline",
    "EvolutionInline",
    "FinancialTransactionInline",
    "IsMinorFilter",
    "PatientAdminActionsMixin",
    "PatientAdminDisplayMixin",
    "SoftDeletedFilter",
]
