"""Exceções de domínio de scheduling."""


class SchedulingDomainError(Exception):
    """Erro controlado do domínio de agendamentos."""


AgendaDomainError = SchedulingDomainError


class CompletedAppointmentDeletionError(SchedulingDomainError):
    """Consulta realizada não pode ser cancelada administrativamente."""


class InvalidRecurrenceScopeError(SchedulingDomainError):
    """Escopo de alteração de recorrência inválido."""


class RecurrenceConflictError(SchedulingDomainError):
    """Alteração de recorrência causaria conflito de horário."""


class CompletedPackageSessionRemovalError(SchedulingDomainError):
    """Sessão realizada de pacote não pode ser removida."""


class TelemedicineUnavailableError(SchedulingDomainError):
    """Sala de telemedicina indisponível, expirada ou revogada."""


__all__ = [
    "AgendaDomainError",
    "CompletedAppointmentDeletionError",
    "CompletedPackageSessionRemovalError",
    "InvalidRecurrenceScopeError",
    "RecurrenceConflictError",
    "SchedulingDomainError",
    "TelemedicineUnavailableError",
]
