"""Compatibilidade para o decorator de feature de billing."""

from .api.v1.decorators import require_feature

__all__ = ["require_feature"]
