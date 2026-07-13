"""Serializers do domínio de documentos."""

from apps.documents.serializers.document_templates import (
    DocumentTemplateListSerializer,
    DocumentTemplateSerializer,
    TemplatePreviewRequestSerializer,
)
from apps.documents.serializers.generated_documents import (
    GeneratedDocumentCreateSerializer,
    GeneratedDocumentDetailSerializer,
    GeneratedDocumentDraftUpdateSerializer,
    GeneratedDocumentListSerializer,
)

__all__ = [
    "DocumentTemplateListSerializer",
    "DocumentTemplateSerializer",
    "TemplatePreviewRequestSerializer",
    "GeneratedDocumentCreateSerializer",
    "GeneratedDocumentDetailSerializer",
    "GeneratedDocumentDraftUpdateSerializer",
    "GeneratedDocumentListSerializer",
]
