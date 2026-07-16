"""Configuração compartilhada do Celery, Redis e tarefas periódicas."""

from celery.schedules import crontab
from kombu import Exchange, Queue

from .base import TIME_ZONE, env

CELERY_BROKER_URL = env(  # noqa: F405
    "CELERY_BROKER_URL",
    default=env("REDIS_URL", default="redis://localhost:6379/0"),  # noqa: F405
)
CELERY_RESULT_BACKEND = env(  # noqa: F405
    "CELERY_RESULT_BACKEND",
    default=env("REDIS_RESULT_URL", default="redis://localhost:6379/1"),  # noqa: F405
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE  # noqa: F405
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = env.int("CELERY_WORKER_PREFETCH_MULTIPLIER", default=1)  # noqa: F405
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "visibility_timeout": env.int("CELERY_VISIBILITY_TIMEOUT_SECONDS", default=3600),  # noqa: F405
    "socket_connect_timeout": 5,
    "socket_timeout": 10,
}
CELERY_RESULT_EXPIRES = env.int("CELERY_RESULT_EXPIRES_SECONDS", default=3600)  # noqa: F405
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_DEFAULT_EXCHANGE = "default"
CELERY_TASK_DEFAULT_ROUTING_KEY = "default"
CELERY_TASK_QUEUES = (
    Queue("default", Exchange("default"), routing_key="default"),
    Queue("exports", Exchange("exports"), routing_key="exports"),
    Queue("uploads", Exchange("uploads"), routing_key="uploads"),
    Queue("communications", Exchange("communications"), routing_key="communications"),
)
CELERY_TASK_ROUTES = {
    "apps.records.tasks.scan_clinical_document": {
        "queue": "uploads",
        "routing_key": "uploads",
    },
    "apps.records.tasks.dispatch_pending_document_scans": {
        "queue": "uploads",
        "routing_key": "uploads",
    },
    "apps.records.tasks.recover_stuck_document_scans": {
        "queue": "uploads",
        "routing_key": "uploads",
    },
    "apps.records.tasks.cleanup_rejected_clinical_documents": {
        "queue": "uploads",
        "routing_key": "uploads",
    },
    "apps.records.tasks.*": {"queue": "exports", "routing_key": "exports"},
    "apps.communications.tasks.*": {
        "queue": "communications",
        "routing_key": "communications",
    },
    "apps.billing.tasks.*": {"queue": "default", "routing_key": "default"},
}
CELERY_TASK_SOFT_TIME_LIMIT = env.int("CELERY_TASK_SOFT_TIME_LIMIT_SECONDS", default=300)  # noqa: F405
CELERY_TASK_TIME_LIMIT = env.int("CELERY_TASK_TIME_LIMIT_SECONDS", default=360)  # noqa: F405
CELERY_BEAT_SCHEDULE = {
    "uploads-dispatch-pending": {
        "task": "apps.records.tasks.dispatch_pending_document_scans",
        "schedule": env.int("CLINICAL_SCAN_DISPATCH_INTERVAL_SECONDS", default=20),  # noqa: F405
        "options": {"queue": "uploads"},
    },
    "uploads-recover-stuck": {
        "task": "apps.records.tasks.recover_stuck_document_scans",
        "schedule": env.int("CLINICAL_SCAN_RECOVERY_INTERVAL_SECONDS", default=120),  # noqa: F405
        "options": {"queue": "uploads"},
    },
    "uploads-cleanup-quarantine": {
        "task": "apps.records.tasks.cleanup_rejected_clinical_documents",
        "schedule": crontab(minute=30),
        "options": {"queue": "uploads"},
    },
    "exports-dispatch-pending": {
        "task": "apps.records.tasks.dispatch_pending_exports",
        "schedule": env.int("EXPORT_DISPATCH_INTERVAL_SECONDS", default=10),  # noqa: F405
        "options": {"queue": "exports"},
    },
    "exports-recover-stuck": {
        "task": "apps.records.tasks.recover_stuck_exports",
        "schedule": env.int("EXPORT_RECOVERY_INTERVAL_SECONDS", default=300),  # noqa: F405
        "options": {"queue": "exports"},
    },
    "exports-expire-files": {
        "task": "apps.records.tasks.expire_clinical_exports",
        "schedule": crontab(minute="*/15"),
        "options": {"queue": "exports"},
    },
    "communications-dispatch-due": {
        "task": "apps.communications.tasks.dispatch_due_communications",
        "schedule": env.int("COMMUNICATIONS_DISPATCH_INTERVAL_SECONDS", default=20),  # noqa: F405
        "options": {"queue": "communications"},
    },
    "communications-schedule-automations": {
        "task": "apps.communications.tasks.schedule_operational_automations",
        "schedule": env.int("COMMUNICATIONS_AUTOMATION_INTERVAL_SECONDS", default=300),  # noqa: F405
        "options": {"queue": "communications"},
    },
    "communications-cleanup-tokens": {
        "task": "apps.communications.tasks.cleanup_expired_public_tokens",
        "schedule": crontab(hour=3, minute=15),
        "options": {"queue": "communications"},
    },
    "billing-dispatch-webhooks": {
        "task": "apps.billing.tasks.dispatch_pending_webhook_events",
        "schedule": env.int("BILLING_WEBHOOK_DISPATCH_INTERVAL_SECONDS", default=15),  # noqa: F405
        "options": {"queue": "default"},
    },
    "billing-reconcile-payments": {
        "task": "apps.billing.tasks.reconcile_asaas_payments",
        "schedule": env.int("BILLING_RECONCILIATION_INTERVAL_MINUTES", default=60) * 60,  # noqa: F405
        "options": {"queue": "default"},
    },
}
