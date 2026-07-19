import os
from datetime import timedelta
from pathlib import Path

import environ
from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY")
AUTH_USER_MODEL = "users.User"

UNFOLD_APPS = [
    "unfold",
    "unfold.contrib.filters",
]
DJANGO_APPS = [
    *UNFOLD_APPS,
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

from django.templatetags.static import static

UNFOLD = {
    "SITE_TITLE": "Elo Terapêutico Admin",
    "SITE_HEADER": "Elo Terapêutico",
    "SITE_URL": "/",
    "COLORS": {
        "primary": {
            "50": "250 245 237",
            "100": "243 232 216",
            "200": "231 206 177",
            "300": "217 172 128",
            "400": "205 137 84",
            "500": "194 108 48",
            "600": "180 86 40",
            "700": "150 67 34",
            "800": "122 55 33",
            "900": "98 47 29",
            "950": "53 23 14",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Geral",
                "separator": True,
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": "/admin/",
                    },
                    {
                        "title": "SQL Explorer",
                        "icon": "database",
                        "link": "/admin/sql-explorer/",
                    },
                ],
            },
            {
                "title": "Clínica & Prontuários",
                "separator": True,
                "items": [
                    {
                        "title": "Pacientes",
                        "icon": "person",
                        "link": "/admin/patients/patient/",
                    },
                    {
                        "title": "Evoluções (Prontuário)",
                        "icon": "description",
                        "link": "/admin/records/evolution/",
                    },
                    {
                        "title": "Anamneses",
                        "icon": "assignment",
                        "link": "/admin/records/anamnesis/",
                    },
                ],
            },
            {
                "title": "Agenda",
                "separator": True,
                "items": [
                    {
                        "title": "Consultas",
                        "icon": "calendar_month",
                        "link": "/admin/agenda/appointment/",
                    },
                    {
                        "title": "Salas Físicas",
                        "icon": "meeting_room",
                        "link": "/admin/agenda/room/",
                    },
                    {
                        "title": "Salas de Telemedicina",
                        "icon": "videocam",
                        "link": "/admin/agenda/telemedicineroom/",
                    },
                ],
            },
            {
                "title": "Financeiro",
                "separator": True,
                "items": [
                    {
                        "title": "Transações",
                        "icon": "attach_money",
                        "link": "/admin/financeiro/financialtransaction/",
                    },
                ],
            },
            {
                "title": "Comunicações",
                "separator": True,
                "items": [
                    {
                        "title": "Comunicações",
                        "icon": "forum",
                        "link": "/admin/communications/communication/",
                    },
                    {
                        "title": "Tentativas",
                        "icon": "sync",
                        "link": "/admin/communications/communicationattempt/",
                    },
                    {
                        "title": "Templates",
                        "icon": "text_snippet",
                        "link": "/admin/communications/communicationtemplate/",
                    },
                    {
                        "title": "Automações",
                        "icon": "automation",
                        "link": "/admin/communications/communicationautomation/",
                    },
                    {
                        "title": "Preferências",
                        "icon": "contact_mail",
                        "link": "/admin/communications/communicationpreference/",
                    },
                    {
                        "title": "Notificações",
                        "icon": "notifications",
                        "link": "/admin/communications/inappnotification/",
                    },
                    {
                        "title": "Canais",
                        "icon": "settings_input_antenna",
                        "link": "/admin/communications/communicationchannelconfig/",
                    },
                ],
            },
            {
                "title": "Billing",
                "separator": True,
                "items": [
                    {
                        "title": "Planos",
                        "icon": "workspace_premium",
                        "link": "/admin/billing/plan/",
                    },
                    {
                        "title": "Assinaturas",
                        "icon": "subscriptions",
                        "link": "/admin/billing/subscription/",
                    },
                    {
                        "title": "Pagamentos",
                        "icon": "payments",
                        "link": "/admin/billing/payment/",
                    },
                    {
                        "title": "Webhooks",
                        "icon": "webhook",
                        "link": "/admin/billing/webhookevent/",
                    },
                ],
            },
            {
                "title": "Administração do Sistema",
                "separator": True,
                "items": [
                    {
                        "title": "Terapeutas / Usuários",
                        "icon": "manage_accounts",
                        "link": "/admin/users/user/",
                    },
                    {
                        "title": "Auditoria",
                        "icon": "security",
                        "link": "/admin/audit/auditlog/",
                    },
                    {
                        "title": "Documentos (Modelos)",
                        "icon": "folder",
                        "link": "/admin/documents/documenttemplate/",
                    },
                    {
                        "title": "Formulários Customizados",
                        "icon": "dynamic_form",
                        "link": "/admin/forms/formtemplate/",
                    },
                ],
            },
        ],
    },
    "ENVIRONMENT": "apps.core.admin_dashboard.environment_callback",
    "DASHBOARD_CALLBACK": "apps.core.admin_dashboard.dashboard_callback",
}
THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]
LOCAL_APPS = [
    "apps.core.apps.CoreConfig",
    "apps.users",
    "apps.patients",
    "apps.records",
    "apps.scheduling.apps.SchedulingConfig",
    "apps.financeiro",
    "apps.documents",
    "apps.reports",
    "apps.forms",
    "apps.billing",
    "apps.communications",
    "apps.audit",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOW_HEADERS = [
    *default_headers,
    "idempotency-key",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "apps" / "core" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DATABASES = {"default": env.db("DATABASE_URL")}
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "elo-cache",
    }
}
RATELIMIT_USE_CACHE = "default"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("apps.billing.authentication.SubscriptionJWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.api.pagination.StandardResultsPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
}
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=30)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env("JWT_SECRET"),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "CHECK_REVOKE_TOKEN": True,  # nosec B105 -- boolean de configuração do SimpleJWT
    "REVOKE_TOKEN_CLAIM": "hash_password",  # nosec B105 -- nome público de claim, não senha
}
PASSWORD_RESET_TIMEOUT = env.int("PASSWORD_RESET_TIMEOUT", default=900)
SPECTACULAR_SETTINGS = {
    "TITLE": "Elo Terapêutico API",
    "DESCRIPTION": "API REST para gestão de consultórios e clínicas de terapia.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "CONTACT": {"name": "Suporte", "email": "suporte@eloterapeutico.com.br"},
    "LICENSE": {"name": "Proprietário"},
    "TAGS": [
        {"name": "auth", "description": "Autenticação e controle de acesso"},
        {"name": "users", "description": "Perfil e configurações do terapeuta"},
        {"name": "patients", "description": "Gestão de pacientes"},
        {"name": "records", "description": "Prontuário eletrônico e evoluções"},
        {"name": "agenda", "description": "Agendamentos e consultas"},
        {"name": "financeiro", "description": "Financeiro e pagamentos"},
        {"name": "documents", "description": "Templates e documentos gerados"},
        {"name": "reports", "description": "Relatórios gerenciais"},
        {"name": "forms", "description": "Formulários personalizados"},
        {"name": "billing", "description": "Planos, assinaturas, pagamentos e webhooks"},
        {
            "name": "communications",
            "description": "Comunicações, notificações, templates e automações",
        },
    ],
}
LOCAL_FIELD_ENCRYPTION_KEY = "elo-terapeutico-local-development-key"
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY", default=LOCAL_FIELD_ENCRYPTION_KEY)
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
AZURE_STORAGE_CONNECTION_STRING = env("AZURE_STORAGE_CONNECTION_STRING", default="")
AZURE_CONTAINER_NAME = env("AZURE_CONTAINER_NAME", default="elo-terapeutico")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@eloterapeutico.com.br")
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=15)
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")
DOCUMENT_CLINIC_NAME = env("DOCUMENT_CLINIC_NAME", default="Elo Terapêutico")
DOCUMENT_CLINIC_ADDRESS = env("DOCUMENT_CLINIC_ADDRESS", default="")
DOCUMENT_CLINIC_PHONE = env("DOCUMENT_CLINIC_PHONE", default="")

COMMUNICATIONS_ENABLED = env.bool("COMMUNICATIONS_ENABLED", default=True)
COMMUNICATIONS_BATCH_SIZE = env.int("COMMUNICATIONS_BATCH_SIZE", default=50)
COMMUNICATIONS_MAX_ATTEMPTS = env.int("COMMUNICATIONS_MAX_ATTEMPTS", default=5)
COMMUNICATIONS_PROCESSING_TIMEOUT_MINUTES = env.int(
    "COMMUNICATIONS_PROCESSING_TIMEOUT_MINUTES",
    default=15,
)
COMMUNICATIONS_DEFAULT_TIMEZONE = env(
    "COMMUNICATIONS_DEFAULT_TIMEZONE",
    default="America/Sao_Paulo",
)
COMMUNICATIONS_REPLY_TO = env("COMMUNICATIONS_REPLY_TO", default="")
WHATSAPP_PROVIDER = env("WHATSAPP_PROVIDER", default="")
WHATSAPP_API_BASE_URL = env("WHATSAPP_API_BASE_URL", default="")
WHATSAPP_ACCESS_TOKEN = env("WHATSAPP_ACCESS_TOKEN", default="")
WHATSAPP_PHONE_NUMBER_ID = env("WHATSAPP_PHONE_NUMBER_ID", default="")
WHATSAPP_WEBHOOK_VERIFY_TOKEN = env("WHATSAPP_WEBHOOK_VERIFY_TOKEN", default="")
WHATSAPP_APP_SECRET = env("WHATSAPP_APP_SECRET", default="")
SMS_PROVIDER = env("SMS_PROVIDER", default="")
SMS_API_KEY = env("SMS_API_KEY", default="")
SMS_SENDER = env("SMS_SENDER", default="")

ASAAS_API_KEY = os.environ.get("ASAAS_API_KEY", "")
ASAAS_BASE_URL = env("ASAAS_BASE_URL", default="https://api-sandbox.asaas.com/v3")
ASAAS_WEBHOOK_TOKEN = os.environ.get("ASAAS_WEBHOOK_TOKEN", "")
BILLING_TRIAL_DAYS = env.int("BILLING_TRIAL_DAYS", default=7)
BILLING_DEFAULT_CURRENCY = env("BILLING_DEFAULT_CURRENCY", default="BRL")
