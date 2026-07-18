"""Fachada temporária para compatibilidade dos health checks.

O caminho permanece disponível para os pontos de patch existentes. Novos imports
devem usar ``apps.core.api.views.health`` e ``apps.core.health``.
"""

import redis

from apps.core.api.views.health import liveness, readiness

__all__ = ["liveness", "readiness", "redis"]
