"""Compatibilidade: models clínicos foram movidos para `records.models`."""

from .models import (
    AnamnesisProfile,
    AnamnesisVersion,
    EvolutionClinicalData,
    EvolutionVersion,
)

__all__ = [
    "AnamnesisProfile",
    "AnamnesisVersion",
    "EvolutionClinicalData",
    "EvolutionVersion",
]
