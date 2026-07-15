"""Settings de desenvolvimento."""

from .base import *  # noqa
from .celery import *  # noqa

DEBUG = True

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])  # noqa: F405

# Origens explícitas evitam esconder erros de CORS durante o desenvolvimento.
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list(  # noqa: F405
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:3000"],
)
CORS_ALLOW_CREDENTIALS = False

# Banco de dados local (Usa a DATABASE_URL definida no .env, com fallback para SQLite)
DATABASES = {"default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3")}  # noqa: F405

# Redis é opcional fora do Docker; quando configurado, cache e Celery usam o mesmo serviço.
_redis_url = env("REDIS_URL", default="")  # noqa: F405
if _redis_url:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": _redis_url,
        }
    }

# E-mail – exibir no console em dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Desabilitar rate limiting em dev
RATELIMIT_ENABLE = False

# Django Debug Toolbar
INSTALLED_APPS += ["debug_toolbar"]  # noqa
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa
INTERNAL_IPS = ["127.0.0.1"]

# Logging detalhado em desenvolvimento
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",  # Mudar para DEBUG para ver queries SQL
            "propagate": False,
        },
    },
}
