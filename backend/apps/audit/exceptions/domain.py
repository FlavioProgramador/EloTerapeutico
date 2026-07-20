"""Exceções do domínio de auditoria."""


class AuditDomainError(Exception):
    """Erro base do domínio de auditoria."""


class AuditLogImmutableError(AuditDomainError, PermissionError):
    """Tentativa de alterar ou remover um evento append-only."""


class InvalidAuditActionError(AuditDomainError):
    """Ação de auditoria inexistente ou não suportada."""


class InvalidAuditMetadataError(AuditDomainError):
    """Metadados de auditoria inválidos ou inseguros."""


class AuditWriteError(AuditDomainError):
    """Falha ao persistir um evento quando a política exige bloqueio."""


class AuditAccessDeniedError(AuditDomainError, PermissionError):
    """Acesso não autorizado à trilha de auditoria."""
