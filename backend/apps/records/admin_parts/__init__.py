"""Registros administrativos do app de prontuários."""

from .addendum import EvolutionAddendumAdmin
from .anamnesis import AnamnesisAdmin
from .evolution import EvolutionAdmin
from .inlines import EvolutionAddendumInline

__all__ = [
    "AnamnesisAdmin",
    "EvolutionAddendumAdmin",
    "EvolutionAddendumInline",
    "EvolutionAdmin",
]
