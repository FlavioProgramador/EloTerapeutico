"""Endpoints HTTP dos health checks globais."""

from __future__ import annotations

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

from apps.core.health.services import collect_readiness_checks


@require_GET
def liveness(request: HttpRequest) -> JsonResponse:
    """Indica que o processo web está ativo, sem dependências externas."""

    return JsonResponse({"status": "ok", "service": "api"})


@require_GET
def readiness(request: HttpRequest) -> JsonResponse:
    """Indica se as dependências técnicas obrigatórias estão disponíveis."""

    healthy, checks = collect_readiness_checks()
    return JsonResponse(
        {"status": "ok" if healthy else "unavailable", "checks": checks},
        status=200 if healthy else 503,
    )
