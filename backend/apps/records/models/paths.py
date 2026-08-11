"""Caminhos de upload do domínio clínico."""

from pathlib import Path
from uuid import uuid4


def _tenant_prefix(instance) -> str:
    organization_id = getattr(instance, "organization_id", None)
    if not organization_id:
        raise ValueError("O arquivo clínico precisa de uma organização antes do upload.")
    return str(organization_id)


def clinical_document_path(instance, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return (
        f"clinical_documents/{_tenant_prefix(instance)}/"
        f"{instance.patient_id}/{uuid4().hex}{suffix}"
    )


def clinical_document_quarantine_path(instance, filename: str) -> str:
    """Mantém arquivos ainda não analisados fora do prefixo liberado."""

    suffix = Path(filename).suffix.lower()
    return (
        f"clinical_quarantine/{_tenant_prefix(instance)}/"
        f"{instance.patient_id}/{uuid4().hex}{suffix}"
    )


def clinical_export_path(instance, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return (
        f"clinical_exports/{_tenant_prefix(instance)}/"
        f"{instance.patient_id}/{uuid4().hex}{suffix}"
    )


# Mantém os caminhos históricos serializados nas migrations existentes.
clinical_document_path.__module__ = "apps.records.treatment_models"
clinical_document_quarantine_path.__module__ = "apps.records.treatment_models"
clinical_export_path.__module__ = "apps.records.treatment_models"
