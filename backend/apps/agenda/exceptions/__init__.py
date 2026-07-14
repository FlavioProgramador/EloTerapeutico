"""Exceções de domínio da Agenda."""


class AgendaDomainError(Exception):
    """Erro controlado do domínio de agenda."""


class CompletedAppointmentDeletionError(AgendaDomainError):
    """Consulta realizada não pode ser cancelada por exclusão administrativa."""


__all__ = ["AgendaDomainError", "CompletedAppointmentDeletionError"]
