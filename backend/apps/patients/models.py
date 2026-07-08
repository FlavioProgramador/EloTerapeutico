"""Fachada de compatibilidade para os modelos de pacientes.

Os modelos ficam organizados em `model_parts/`, mantendo imports públicos como
`from apps.patients.models import Patient` sem alterações no restante do projeto.
"""

from .model_parts import (
    AllPatientsManager,
    Patient,
    PatientManager,
    PatientProfessional,
    PatientRegistrationInvite,
    patient_photo_path,
)

__all__ = [
    "AllPatientsManager",
    "Patient",
    "PatientManager",
    "PatientProfessional",
    "PatientRegistrationInvite",
    "patient_photo_path",
]
