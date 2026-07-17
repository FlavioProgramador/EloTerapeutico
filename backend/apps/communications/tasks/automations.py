"""Tasks de agendamento das automações operacionais."""

from __future__ import annotations

from celery import shared_task
from django.conf import settings

from apps.communications.services.scheduled_operations import (
    schedule_operational_automations,
)


@shared_task(
    name="apps.communications.tasks.schedule_operational_automations",
    acks_late=True,
    ignore_result=True,
    soft_time_limit=180,
    time_limit=240,
)
def schedule_operational_automations_task() -> dict[str, int]:
    return schedule_operational_automations(
        due_days=max(
            int(getattr(settings, "COMMUNICATIONS_PAYMENT_DUE_DAYS", 3)),
            0,
        ),
        form_reminder_hours=max(
            int(getattr(settings, "COMMUNICATIONS_FORM_REMINDER_HOURS", 24)),
            1,
        ),
        document_reminder_hours=max(
            int(
                getattr(
                    settings,
                    "COMMUNICATIONS_DOCUMENT_REMINDER_HOURS",
                    24,
                )
            ),
            1,
        ),
    )
