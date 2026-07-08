"""Settings de desenvolvimento."""

from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# CORS – Permite qualquer origem em desenvolvimento
CORS_ALLOW_ALL_ORIGINS = True

# Banco de dados local (Usa a DATABASE_URL definida no .env, com fallback para SQLite)
DATABASES = {"default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3")}

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
