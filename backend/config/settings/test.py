# mypy: ignore-errors
"""Configurações determinísticas e rápidas para a suíte de testes."""

from django.utils.crypto import get_random_string

from apps.core.admin_sql_config import configure_unfold_navigation

from .base import *  # noqa: F403,F401
from .celery import *  # noqa: F403,F401

DEBUG = False
AUTH_REQUIRE_SESSION_CLAIM = False
TENANT_ENFORCEMENT_ENABLED = False
INSTALLED_APPS += ["apps.organizations.apps.OrganizationsConfig"]  # noqa: F405
CORS_ALLOW_HEADERS = [*CORS_ALLOW_HEADERS, "x-organization-id"]  # noqa: F405
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.organizations.authentication.TenantSubscriptionJWTAuthentication",
    ),
}

ADMIN_SQL_EXPLORER_ENABLED = False
ADMIN_SQL_EXPLORER_DATABASE_ALIAS = "default"
ADMIN_SQL_EXPLORER_MAX_ROWS = 100
ADMIN_SQL_EXPLORER_TIMEOUT_MS = 2_000
ADMIN_SQL_EXPLORER_ALLOWED_TABLES = []
ADMIN_SQL_EXPLORER_PERMISSION = "core.use_sql_explorer"
configure_unfold_navigation(UNFOLD, enabled=False)  # noqa: F405

ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test.sqlite3",  # noqa: F405
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

MEDIA_ROOT = BASE_DIR / ".test-media"  # noqa: F405

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = []

# Celery executa em memória e de forma síncrona nos testes.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"
HEALTH_CHECK_STORAGE = False

# Valores sintéticos aleatórios impedem dependência de credenciais ou rede reais.
ASAAS_API_KEY = f"test-{get_random_string(32)}"
ASAAS_BASE_URL = "https://api-sandbox.asaas.com/v3"
ASAAS_WEBHOOK_TOKEN = get_random_string(32)
BILLING_ENABLED = True
BILLING_WEBHOOK_PROCESS_INLINE = True

RATELIMIT_ENABLE = False
BILLING_ENFORCE_PATIENT_LIMITS = False
BILLING_REQUIRE_SUBSCRIPTION = False
