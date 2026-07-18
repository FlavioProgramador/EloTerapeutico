"""Orquestração dos health checks transversais."""

from __future__ import annotations

from django.conf import settings

from .checks import check_database, check_redis, check_storage


def collect_readiness_checks() -> tuple[bool, dict[str, str]]:
    """Executa os checks habilitados e retorna saúde agregada e detalhes."""

    checks = {
        "database": "ok" if check_database() else "error",
        "redis": "ok" if check_redis() else "error",
    }

    if getattr(settings, "HEALTH_CHECK_STORAGE", False):
        checks["storage"] = "ok" if check_storage() else "error"

    return all(status == "ok" for status in checks.values()), checks
