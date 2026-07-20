"""Contrato público de escrita da auditoria."""

from .events import log_access, record_audit_event
from .request_context import extract_request_context
from .sanitization import clean_text, safe_resource_repr, sanitize_metadata

__all__ = [
    "clean_text",
    "extract_request_context",
    "log_access",
    "record_audit_event",
    "safe_resource_repr",
    "sanitize_metadata",
]
