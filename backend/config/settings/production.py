"""Settings de produção para Azure App Service e containers."""

from typing import Any, cast

from django.core.exceptions import ImproperlyConfigured

from apps.core.admin_sql_config import configure_unfold_navigation
from apps.core.security_config import require_distinct_secrets, require_strong_secret

from .base import *  # noqa: F401,F403
from .celery import *  # noqa: F401,F403

DEBUG = False

if env.bool("ADMIN_SQL_EXPLORER_ENABLED", default=False):  # noqa: F405
    raise ImproperlyConfigured("ADMIN_SQL_EXPLORER_ENABLED deve permanecer False em produção.")
ADMIN_SQL_EXPLORER_ENABLED = False
ADMIN_SQL_EXPLORER_DATABASE_ALIAS = "default"
ADMIN_SQL_EXPLORER_MAX_ROWS = 100
ADMIN_SQL_EXPLORER_TIMEOUT_MS = 2_000
ADMIN_SQL_EXPLORER_ALLOWED_TABLES: list[str] = []
ADMIN_SQL_EXPLORER_PERMISSION = "core.use_sql_explorer"
configure_unfold_navigation(UNFOLD, enabled=False)  # noqa: F405

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # noqa: F405

require_strong_secret("SECRET_KEY", SECRET_KEY)  # noqa: F405
require_strong_secret("JWT_SECRET", SIMPLE_JWT["SIGNING_KEY"])  # noqa: F405
require_strong_secret(
    "FIELD_ENCRYPTION_KEY",
    FIELD_ENCRYPTION_KEY,  # noqa: F405
    forbidden_values={LOCAL_FIELD_ENCRYPTION_KEY},  # noqa: F405
)
require_strong_secret("ASAAS_WEBHOOK_TOKEN", ASAAS_WEBHOOK_TOKEN)  # noqa: F405
require_distinct_secrets(
    {
        "SECRET_KEY": SECRET_KEY,  # noqa: F405
        "JWT_SECRET": SIMPLE_JWT["SIGNING_KEY"],  # noqa: F405
        "FIELD_ENCRYPTION_KEY": FIELD_ENCRYPTION_KEY,  # noqa: F405
        "ASAAS_WEBHOOK_TOKEN": ASAAS_WEBHOOK_TOKEN,  # noqa: F405
    }
)

if "sandbox" in ASAAS_BASE_URL.lower():  # noqa: F405
    raise ImproperlyConfigured("ASAAS_BASE_URL não pode apontar para sandbox em produção.")

if not ASAAS_API_KEY:  # noqa: F405
    raise ImproperlyConfigured("ASAAS_API_KEY deve ser configurada em produção.")

# Multi-tenancy é obrigatório em produção. O app é registrado aqui para manter
# compatibilidade com settings legados de desenvolvimento durante a migração.
if "apps.organizations.apps.OrganizationsConfig" not in INSTALLED_APPS:  # noqa: F405
    INSTALLED_APPS.insert(2, "apps.organizations.apps.OrganizationsConfig")  # noqa: F405
REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = (  # noqa: F405
    "apps.organizations.authentication.TenantSubscriptionJWTAuthentication",
)
if "x-organization-id" not in CORS_ALLOW_HEADERS:  # noqa: F405
    CORS_ALLOW_HEADERS.append("x-organization-id")  # noqa: F405
TENANT_ENFORCEMENT_ENABLED = True

# Segurança e proxy reverso
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
TRUST_PROXY_CLIENT_IP_HEADERS = env.bool("TRUST_PROXY_CLIENT_IP_HEADERS", default=False)  # noqa: F405
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

# CORS e CSRF
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = False
_cors = env.list("CORS_ALLOWED_ORIGINS", default=[])  # noqa: F405
if not _cors:
    raise ImproperlyConfigured("CORS_ALLOWED_ORIGINS deve ser configurada explicitamente em produção.")
CORS_ALLOWED_ORIGINS = _cors
CSRF_TRUSTED_ORIGINS = env.list(  # noqa: F405
    "CSRF_TRUSTED_ORIGINS",
    default=[],
)

# Banco de dados
DATABASES = {  # noqa: F405
    "default": env.db("DATABASE_URL"),  # noqa: F405
}
DATABASES["default"].update(
    {
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
    }
)

# Redis é obrigatório em produção para cache, rate limit e Celery.
_redis_url = env("REDIS_URL")  # noqa: F405
CACHES = cast(
    dict[str, dict[str, Any]],
    {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _redis_url,
            "OPTIONS": {
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
            },
        }
    },
)
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=_redis_url)  # noqa: F405
CELERY_RESULT_BACKEND = env(  # noqa: F405
    "CELERY_RESULT_BACKEND",
    default=env("REDIS_RESULT_URL", default=_redis_url),  # noqa: F405
)

# Arquivos estáticos e mídia privada
if "whitenoise.runserver_nostatic" not in INSTALLED_APPS:  # noqa: F405
    INSTALLED_APPS.insert(0, "whitenoise.runserver_nostatic")  # noqa: F405
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STORAGES: dict[str, dict[str, Any]] = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

_private_media_required = env.bool("PRIVATE_MEDIA_STORAGE_REQUIRED", default=True)  # noqa: F405
if AZURE_STORAGE_CONNECTION_STRING:  # noqa: F405
    STORAGES["default"] = {
        "BACKEND": "storages.backends.azure_storage.AzureStorage",
        "OPTIONS": {
            "connection_string": AZURE_STORAGE_CONNECTION_STRING,  # noqa: F405
            "azure_container": AZURE_CONTAINER_NAME,  # noqa: F405
            "expiration_secs": env.int("AZURE_URL_EXPIRATION_SECS", default=300),  # noqa: F405
            "overwrite_files": False,
        },
    }
elif _private_media_required:
    raise ImproperlyConfigured(
        "AZURE_STORAGE_CONNECTION_STRING deve ser configurada quando "
        "PRIVATE_MEDIA_STORAGE_REQUIRED=True."
    )

HEALTH_CHECK_STORAGE = env.bool("HEALTH_CHECK_STORAGE", default=False)  # noqa: F405
RATELIMIT_ENABLE = True

# Logging estruturado para Azure Monitor
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "structlog.stdlib.ProcessorFormatter",
            "processor": "structlog.processors.JSONRenderer",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.security": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

# E-mail
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.sendgrid.net")  # noqa: F405
EMAIL_PORT = env.int("EMAIL_PORT", default=587)  # noqa: F405
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")  # noqa: F405
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")  # noqa: F405
