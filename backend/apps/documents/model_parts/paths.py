"""Caminhos de upload do módulo de documentos."""

from __future__ import annotations

from pathlib import Path


def generated_document_path(instance, filename: str) -> str:
    """Gera um caminho não previsível sem dados pessoais no nome do arquivo."""

    suffix = Path(filename).suffix.lower() or ".pdf"
    return f"generated_documents/{instance.owner_id}/{instance.public_id.hex}{suffix}"


# Mantém o caminho serializado em migrations antigas mesmo após mover o código.
generated_document_path.__module__ = "apps.documents.models"
