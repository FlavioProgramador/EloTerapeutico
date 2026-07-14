"""Exceções de domínio da Agenda."""


class AgendaDomainError(Exception):
    """Erro controlado do domínio de agenda."""


class CompletedAppointmentDeletionError(AgendaDomainError):
    """Consulta realizada não pode ser cancelada por exclusão administrativa."""


class InvalidRecurrenceScopeError(AgendaDomainError):
    """Escopo de alteração de recorrência inválido."""


class RecurrenceConflictError(AgendaDomainError):
    """Alteração de recorrência causaria conflito de horário."""


__all__ = [
    "AgendaDomainError",
    "CompletedAppointmentDeletionError",
    "InvalidRecurrenceScopeError",
    "RecurrenceConflictError",
]
