"""Health checks compartilhados e superfície pública de compatibilidade."""

from __future__ import annotations

from typing import Any

import redis

from .services import collect_readiness_checks


def liveness(request: Any):
    """Encaminha chamadas legadas para a view canônica de liveness."""

    from apps.core.api.views.health import liveness as liveness_view

    return liveness_view(request)


def readiness(request: Any):
    """Encaminha chamadas legadas para a view canônica de readiness."""

    from apps.core.api.views.health import readiness as readiness_view

    return readiness_view(request)


__all__ = ["collect_readiness_checks", "liveness", "readiness", "redis"]
