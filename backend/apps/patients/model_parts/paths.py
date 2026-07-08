"""Caminhos de upload do domínio de pacientes."""

from pathlib import Path
from uuid import uuid4


def patient_photo_path(instance, filename: str) -> str:
    """Gera nome não previsível sem expor o nome do paciente no storage."""

    suffix = Path(filename).suffix.lower()
    owner = instance.therapist_id or "unassigned"
    return f"patient_photos/{owner}/{uuid4().hex}{suffix}"


# Mantém o caminho serializado em migrations antigas mesmo após mover o código.
patient_photo_path.__module__ = "apps.patients.models"
