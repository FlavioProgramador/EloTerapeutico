"""Regras modulares do verificador arquitetural."""

from .audit import validate_audit_architecture
from .core import validate_core_architecture
from .documents import validate_documents_architecture
from .finances import validate_finances_architecture
from .scheduling import validate_scheduling_architecture

__all__ = [
    "validate_audit_architecture",
    "validate_core_architecture",
    "validate_documents_architecture",
    "validate_finances_architecture",
    "validate_scheduling_architecture",
]
