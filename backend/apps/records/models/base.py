"""Fachada de compatibilidade para modelos base do prontuário."""

from .addendum import EvolutionAddendum
from .anamnesis import Anamnesis
from .evolution import Evolution

__all__ = ["Anamnesis", "Evolution", "EvolutionAddendum"]
