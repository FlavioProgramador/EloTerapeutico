"""Regras modulares do verificador arquitetural."""

from .core import validate_core_architecture
from .documents import validate_documents_architecture

__all__ = ["validate_core_architecture", "validate_documents_architecture"]
