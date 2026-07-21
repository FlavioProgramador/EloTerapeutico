"""Caminhos de upload do módulo de documentos."""

from __future__ import annotations

from pathlib import Path


def generated_document_path(instance, filename: str) -> str:
    """Gera caminho privado por organização, sem dados pessoais no nome."""

    suffix = Path(filename).suffix.lower() or ".pdf"
    return (
        f"organizations/{instance.organization_id}/generated_documents/"
        f"{instance.public_id.hex}{suffix}"
    )


# Mantém o caminho serializado em migrations antigas mesmo após mover o código.
generated_document_path.__module__ = "apps.documents.models"
