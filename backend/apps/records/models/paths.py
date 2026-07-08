"""Caminhos de upload do domínio clínico."""

from pathlib import Path
from uuid import uuid4


def clinical_document_path(instance, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"clinical_documents/{instance.patient_id}/{uuid4().hex}{suffix}"


def clinical_export_path(instance, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"clinical_exports/{instance.patient_id}/{uuid4().hex}{suffix}"


# Mantém os caminhos históricos serializados nas migrations existentes.
clinical_document_path.__module__ = "apps.records.treatment_models"
clinical_export_path.__module__ = "apps.records.treatment_models"
