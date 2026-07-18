"""Registros administrativos do domínio documental."""

from .document_sequences import DocumentSequenceAdmin
from .document_templates import DocumentTemplateAdmin
from .generated_documents import GeneratedDocumentAdmin

__all__ = [
    "DocumentSequenceAdmin",
    "DocumentTemplateAdmin",
    "GeneratedDocumentAdmin",
]
