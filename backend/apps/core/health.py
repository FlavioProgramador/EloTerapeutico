"""Health checks leves para orquestradores e balanceadores."""

from __future__ import annotations

import logging

import redis
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@require_GET
def liveness(request):
    return JsonResponse({"status": "ok", "service": "api"})


@require_GET
def readiness(request):
    checks: dict[str, str] = {}
    healthy = True

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["database"] = "ok"
    except Exception as exc:
        healthy = False
        checks["database"] = "error"
        logger.warning("readiness_database_failed", extra={"exception_type": exc.__class__.__name__})

    redis_client = None
    try:
        redis_client = redis.Redis.from_url(
            settings.CELERY_BROKER_URL,
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=False,
        )
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        healthy = False
        checks["redis"] = "error"
        logger.warning("readiness_redis_failed", extra={"exception_type": exc.__class__.__name__})
    finally:
        if redis_client is not None:
            redis_client.close()

    if getattr(settings, "HEALTH_CHECK_STORAGE", False):
        try:
            default_storage.exists("health/readiness-probe")
            checks["storage"] = "ok"
        except Exception as exc:
            healthy = False
            checks["storage"] = "error"
            logger.warning("readiness_storage_failed", extra={"exception_type": exc.__class__.__name__})

    return JsonResponse(
        {"status": "ok" if healthy else "unavailable", "checks": checks},
        status=200 if healthy else 503,
    )
