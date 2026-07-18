"""Fachada temporária das permissões públicas de documentos."""

from apps.documents.api.v1.permissions import IsClinicalDocumentUser

__all__ = ["IsClinicalDocumentUser"]
