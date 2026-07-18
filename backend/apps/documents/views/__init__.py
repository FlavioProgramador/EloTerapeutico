"""Fachada temporária das views públicas de documentos."""

from apps.documents.api.v1.views import (
    DocumentLibraryViewSet,
    DocumentTemplateViewSet,
    GeneratedDocumentViewSet,
    PlaceholderListView,
)

__all__ = [
    "DocumentLibraryViewSet",
    "DocumentTemplateViewSet",
    "GeneratedDocumentViewSet",
    "PlaceholderListView",
]
