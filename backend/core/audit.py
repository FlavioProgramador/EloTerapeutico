"""Compatibilidade para imports antigos; use `apps.core.audit`."""

from apps.core.audit import AuditLog, AuditLogMixin, log_access

__all__ = ["AuditLog", "AuditLogMixin", "log_access"]
