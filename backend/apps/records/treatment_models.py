"""Compatibilidade para migrations e imports históricos do prontuário."""

from .models import (
    ClinicalDocument,
    ClinicalExport,
    ClinicalFormResponse,
    TreatmentGoal,
    clinical_document_path,
    clinical_export_path,
)

__all__ = [
    "ClinicalDocument",
    "ClinicalExport",
    "ClinicalFormResponse",
    "TreatmentGoal",
    "clinical_document_path",
    "clinical_export_path",
]
