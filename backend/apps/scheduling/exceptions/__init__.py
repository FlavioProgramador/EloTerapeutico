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


class TelemedicineDisabledError(TelemedicineUnavailableError):
    """Telemedicina desligada globalmente ou pela organização."""


class TelemedicineProviderUnavailableError(TelemedicineUnavailableError):
    """Provedor de mídia indisponível ou sem configuração válida."""


class TelemedicineAccessDeniedError(TelemedicineUnavailableError):
    """Ator não possui acesso à sala solicitada."""


class TelemedicineOutsideJoinWindowError(TelemedicineUnavailableError):
    """Tentativa de entrada fora da janela permitida."""


class TelemedicineConsentRequiredError(TelemedicineUnavailableError):
    """Consentimento versionado ainda não foi aceito."""


class TelemedicineInvitationExpiredError(TelemedicineUnavailableError):
    """Convite público inválido, revogado ou expirado."""


class TelemedicineInvalidStateError(TelemedicineUnavailableError):
    """Estado atual da sala não permite a operação."""


class TelemedicineEncryptionUnavailableError(TelemedicineUnavailableError):
    """A chamada não pode iniciar com a proteção E2EE exigida."""


__all__ = [
    "AgendaDomainError",
    "CompletedAppointmentDeletionError",
    "CompletedPackageSessionRemovalError",
    "InvalidRecurrenceScopeError",
    "RecurrenceConflictError",
    "SchedulingDomainError",
    "TelemedicineAccessDeniedError",
    "TelemedicineConsentRequiredError",
    "TelemedicineDisabledError",
    "TelemedicineEncryptionUnavailableError",
    "TelemedicineInvitationExpiredError",
    "TelemedicineInvalidStateError",
    "TelemedicineOutsideJoinWindowError",
    "TelemedicineProviderUnavailableError",
    "TelemedicineUnavailableError",
]
