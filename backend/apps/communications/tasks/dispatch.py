"""Tasks de despacho de comunicações."""

from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.communications.models import Communication
from apps.communications.services.dispatch import (
    claim_due_communications,
    dispatch_communication,
)


@shared_task(
    bind=True,
    name="apps.communications.tasks.send_communication",
    acks_late=True,
    reject_on_worker_lost=True,
    ignore_result=True,
    max_retries=3,
    soft_time_limit=60,
    time_limit=90,
)
def send_communication(self, communication_id: int) -> None:
    try:
        dispatch_communication(communication_id)
    except Exception as exc:
        countdown = min(30 * (2**self.request.retries), 300)
        final = self.request.retries >= self.max_retries
        updates = {
            "status": (
                Communication.Status.FAILED
                if final
                else Communication.Status.QUEUED
            ),
            "processing_started_at": None,
            "next_retry_at": (
                None
                if final
                else timezone.now() + timedelta(seconds=countdown)
            ),
        }
        if final:
            updates["failed_at"] = timezone.now()
        Communication.objects.filter(
            pk=communication_id,
            status=Communication.Status.PROCESSING,
        ).update(**updates)
        if final:
            raise
        raise self.retry(
            exc=exc,
            countdown=countdown,
            max_retries=self.max_retries,
        )


@shared_task(
    name="apps.communications.tasks.dispatch_due_communications",
    acks_late=True,
    ignore_result=True,
)
def dispatch_due_communications() -> int:
    communication_ids = claim_due_communications()
    published = 0
    for communication_id in communication_ids:
        try:
            send_communication.apply_async(
                args=[communication_id],
                queue="communications",
            )
            published += 1
        except Exception:
            Communication.objects.filter(
                pk=communication_id,
                status=Communication.Status.PROCESSING,
            ).update(
                status=Communication.Status.QUEUED,
                processing_started_at=None,
                next_retry_at=timezone.now() + timedelta(seconds=30),
            )
    return published
