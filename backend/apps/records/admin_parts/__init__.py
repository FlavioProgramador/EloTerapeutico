"""Registros administrativos do app de prontuários."""

from .addendum import EvolutionAddendumAdmin
from .anamnesis import AnamnesisAdmin
from .documents import ClinicalDocumentAdmin
from .evolution import EvolutionAdmin
from .inlines import EvolutionAddendumInline

__all__ = [
    "AnamnesisAdmin",
    "ClinicalDocumentAdmin",
    "EvolutionAddendumAdmin",
    "EvolutionAddendumInline",
    "EvolutionAdmin",
]
