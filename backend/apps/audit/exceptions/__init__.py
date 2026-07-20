"""Exceções públicas de auditoria."""

from .domain import (
    AuditAccessDeniedError,
    AuditDomainError,
    AuditLogImmutableError,
    AuditWriteError,
    InvalidAuditActionError,
    InvalidAuditMetadataError,
)

__all__ = [
    "AuditAccessDeniedError",
    "AuditDomainError",
    "AuditLogImmutableError",
    "AuditWriteError",
    "InvalidAuditActionError",
    "InvalidAuditMetadataError",
]
