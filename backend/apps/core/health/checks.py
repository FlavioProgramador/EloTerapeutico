"""Checks técnicos reutilizáveis pelo endpoint de readiness."""

from __future__ import annotations

import logging

import redis
from django.conf import settings
from django.core.files.storage import default_storage
from django.db import connection

logger = logging.getLogger(__name__)


def check_database() -> bool:
    """Confirma que o banco aceita uma consulta mínima."""

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception as exc:
        logger.warning(
            "readiness_database_failed",
            extra={"exception_type": exc.__class__.__name__},
        )
        return False


def check_redis() -> bool:
    """Confirma que o broker Redis configurado responde a ping."""

    redis_client = None
    try:
        redis_client = redis.Redis.from_url(
            settings.CELERY_BROKER_URL,
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=False,
        )
        redis_client.ping()
        return True
    except Exception as exc:
        logger.warning(
            "readiness_redis_failed",
            extra={"exception_type": exc.__class__.__name__},
        )
        return False
    finally:
        if redis_client is not None:
            redis_client.close()


def check_storage() -> bool:
    """Confirma que o storage padrão pode ser consultado."""

    try:
        default_storage.exists("health/readiness-probe")
        return True
    except Exception as exc:
        logger.warning(
            "readiness_storage_failed",
            extra={"exception_type": exc.__class__.__name__},
        )
        return False
