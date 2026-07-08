"""Fachada de compatibilidade para modelos de tratamento clínico.

A implementação foi separada em arquivos por domínio dentro de `records.models`,
preservando imports existentes como `from apps.records.models.treatment import ClinicalExport`.
"""

from .documents import ClinicalDocument
from .exports import ClinicalExport
from .forms import ClinicalFormResponse
from .goals import TreatmentGoal
from .paths import clinical_document_path, clinical_export_path

__all__ = [
    "ClinicalDocument",
    "ClinicalExport",
    "ClinicalFormResponse",
    "TreatmentGoal",
    "clinical_document_path",
    "clinical_export_path",
]
