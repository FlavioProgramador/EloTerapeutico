"""Fachada de compatibilidade para modelos de documentos.

Os modelos ficam em `model_parts/`, preservando imports públicos como
`from apps.documents.models import GeneratedDocument`.
"""

from .model_parts import (
    DocumentSequence,
    DocumentTemplate,
    GeneratedDocument,
    generated_document_path,
)

__all__ = [
    "DocumentSequence",
    "DocumentTemplate",
    "GeneratedDocument",
    "generated_document_path",
]
