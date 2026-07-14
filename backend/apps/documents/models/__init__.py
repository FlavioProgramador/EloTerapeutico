"""Modelos do app de documentos organizados por domínio."""

from .generated import GeneratedDocument
from .paths import generated_document_path
from .sequences import DocumentSequence
from .templates import DocumentTemplate

__all__ = [
    "DocumentSequence",
    "DocumentTemplate",
    "GeneratedDocument",
    "generated_document_path",
]
