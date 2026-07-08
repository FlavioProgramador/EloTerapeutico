"""Fachada de compatibilidade para modelos clínicos estruturados."""

from .anamnesis_profile import AnamnesisProfile
from .evolution_clinical_data import EvolutionClinicalData
from .versions import AnamnesisVersion, EvolutionVersion

__all__ = [
    "AnamnesisProfile",
    "AnamnesisVersion",
    "EvolutionClinicalData",
    "EvolutionVersion",
]
