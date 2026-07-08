import os
from datetime import timedelta
from pathlib import Path

import environ
from django.urls import reverse_lazy

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SECRET_KEY = env("SECRET_KEY")
AUTH_USER_MODEL = "users.User"

UNFOLD_APPS = [
    "unfold",
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
THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]
LOCAL_APPS = [
    "apps.core",
    "apps.users",
    "apps.patients",
    "apps.records",
    "apps.agenda",
    "apps.financeiro",
    "apps.documents",
    "apps.reports",
    "apps.forms",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

UNFOLD = {
    "SITE_TITLE": "Elo Terapêutico Admin",
    "SITE_HEADER": "Elo Terapêutico",
    "SITE_SUBHEADER": "Painel interno da plataforma",
    "SITE_SYMBOL": "psychology",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "DASHBOARD_CALLBACK": "apps.core.admin_dashboard.dashboard_callback",
    "ENVIRONMENT": "apps.core.admin_dashboard.environment_callback",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Visão Geral",
                "separator": True,
                "items": [
                    {"title": "Dashboard", "icon": "dashboard", "link": reverse_lazy("admin:index")},
                ],
            },
            {
                "title": "Usuários e Acessos",
                "separator": True,
                "items": [
                    {
                        "title": "Usuários",
                        "icon": "manage_accounts",
                        "link": reverse_lazy("admin:users_user_changelist"),
                    },
                    {
                        "title": "Grupos",
                        "icon": "groups",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                    {
                        "title": "Horários de atendimento",
                        "icon": "schedule",
                        "link": reverse_lazy("admin:users_workinghours_changelist"),
                    },
                ],
            },
            {
                "title": "Pacientes",
                "separator": True,
                "items": [
                    {
                        "title": "Pacientes",
                        "icon": "personal_injury",
                        "link": reverse_lazy("admin:patients_patient_changelist"),
                    },
                ],
            },
            {
                "title": "Agenda",
                "separator": True,
                "items": [
                    {
                        "title": "Agendamentos",
                        "icon": "event",
                        "link": reverse_lazy("admin:agenda_appointment_changelist"),
                    },
                    {
                        "title": "Recorrências",
                        "icon": "event_repeat",
                        "link": reverse_lazy("admin:agenda_appointmentrecurrence_changelist"),
                    },
                    {
                        "title": "Bloqueios de agenda",
                        "icon": "event_busy",
                        "link": reverse_lazy("admin:agenda_scheduleblock_changelist"),
                    },
                    {
                        "title": "Salas",
                        "icon": "meeting_room",
                        "link": reverse_lazy("admin:agenda_room_changelist"),
                    },
                    {
                        "title": "Pacotes de sessões",
                        "icon": "inventory_2",
                        "link": reverse_lazy("admin:agenda_patientpackage_changelist"),
                    },
                    {
                        "title": "Sessões de pacote",
                        "icon": "checklist",
                        "link": reverse_lazy("admin:agenda_packagesession_changelist"),
                    },
                    {
                        "title": "Telemedicina",
                        "icon": "video_call",
                        "link": reverse_lazy("admin:agenda_telemedicineroom_changelist"),
                    },
                    {
                        "title": "Lembretes",
                        "icon": "notifications",
                        "link": reverse_lazy("admin:agenda_appointmentreminder_changelist"),
                    },
                ],
            },
            {
                "title": "Prontuários",
                "separator": True,
                "items": [
                    {
                        "title": "Anamneses",
                        "icon": "assignment",
                        "link": reverse_lazy("admin:records_anamnesis_changelist"),
                    },
                    {
                        "title": "Evoluções",
                        "icon": "clinical_notes",
                        "link": reverse_lazy("admin:records_evolution_changelist"),
                    },
                    {
                        "title": "Aditivos",
                        "icon": "post_add",
                        "link": reverse_lazy("admin:records_evolutionaddendum_changelist"),
                    },
                ],
            },
            {
                "title": "Financeiro",
                "separator": True,
                "items": [
                    {
                        "title": "Transações financeiras",
                        "icon": "payments",
                        "link": reverse_lazy(
                            "admin:financeiro_financialtransaction_changelist"
                        ),
                    },
                ],
            },
            {
                "title": "Documentos",
                "separator": True,
                "items": [
                    {
                        "title": "Templates",
                        "icon": "article",
                        "link": reverse_lazy("admin:documents_documenttemplate_changelist"),
                    },
                    {
                        "title": "Documentos gerados",
                        "icon": "description",
                        "link": reverse_lazy("admin:documents_generateddocument_changelist"),
                    },
                    {
                        "title": "Sequências",
                        "icon": "format_list_numbered",
                        "link": reverse_lazy("admin:documents_documentsequence_changelist"),
                    },
                ],
            },
            {
                "title": "Formulários",
                "separator": True,
                "items": [
                    {
                        "title": "Templates de formulário",
                        "icon": "dynamic_form",
                        "link": reverse_lazy("admin:forms_formtemplate_changelist"),
                    },
                    {
                        "title": "Formulários terapêuticos",
                        "icon": "fact_check",
                        "link": reverse_lazy("admin:forms_therapeuticform_changelist"),
                    },
                    {
                        "title": "Respostas enviadas",
                        "icon": "rate_review",
                        "link": reverse_lazy("admin:forms_formsubmission_changelist"),
                    },
                    {
                        "title": "Itens de resposta",
                        "icon": "subject",
                        "link": reverse_lazy("admin:forms_formanswer_changelist"),
                    },
                ],
            },
        ],
    },
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
ROOT_URLCONF = "elo_terapeutico.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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
WSGI_APPLICATION = "elo_terapeutico.wsgi.application"
ASGI_APPLICATION = "elo_terapeutico.asgi.application"
DATABASES = {"default": env.db("DATABASE_URL")}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardResultsPagination",
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
    "CHECK_REVOKE_TOKEN": True,
    "REVOKE_TOKEN_CLAIM": "hash_password",
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
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")
DOCUMENT_CLINIC_NAME = env("DOCUMENT_CLINIC_NAME", default="Elo Terapêutico")
DOCUMENT_CLINIC_ADDRESS = env("DOCUMENT_CLINIC_ADDRESS", default="")
DOCUMENT_CLINIC_PHONE = env("DOCUMENT_CLINIC_PHONE", default="")
