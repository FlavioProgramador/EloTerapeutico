"""Tasks de processamento e despacho de webhooks de billing."""

from __future__ import annotations

import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.billing.integrations.asaas.webhooks import process_webhook_event
from apps.billing.models import WebhookEvent

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="apps.billing.tasks.process_webhook_event",
    acks_late=True,
    reject_on_worker_lost=True,
    ignore_result=True,
    max_retries=3,
    soft_time_limit=90,
    time_limit=120,
)
def process_webhook_event_task(self, event_id: int) -> None:
    try:
        event = WebhookEvent.objects.get(pk=event_id)
        process_webhook_event(event)
    except WebhookEvent.DoesNotExist:
        return
    except Exception as exc:
        countdown = min(30 * (2**self.request.retries), 300)
        WebhookEvent.objects.filter(pk=event_id).exclude(
            status__in=[
                WebhookEvent.Status.PROCESSED,
                WebhookEvent.Status.IGNORED,
            ]
        ).update(
            status=WebhookEvent.Status.RETRY,
            next_retry_at=timezone.now() + timedelta(seconds=countdown),
            last_error="Falha temporária ao despachar o evento.",
            error_message="Falha temporária ao despachar o evento.",
        )
        if self.request.retries >= self.max_retries:
            raise
        raise self.retry(
            exc=exc,
            countdown=countdown,
            max_retries=self.max_retries,
        )


@shared_task(
    name="apps.billing.tasks.dispatch_pending_webhook_events",
    acks_late=True,
    ignore_result=True,
)
def dispatch_pending_webhook_events() -> int:
    """Reserva eventos no PostgreSQL e publica apenas seus IDs no broker."""

    now = timezone.now()
    batch_size = max(
        int(getattr(settings, "BILLING_WEBHOOK_DISPATCH_BATCH_SIZE", 50)),
        1,
    )
    reservation_timeout = max(
        int(
            getattr(
                settings,
                "BILLING_WEBHOOK_RESERVATION_TIMEOUT_MINUTES",
                5,
            )
        ),
        1,
    )
    reserved: list[int] = []

    with transaction.atomic():
        queryset = (
            WebhookEvent.objects.select_for_update(skip_locked=True)
            .filter(
                Q(
                    status__in=[
                        WebhookEvent.Status.RECEIVED,
                        WebhookEvent.Status.RETRY,
                    ]
                )
                | Q(
                    status=WebhookEvent.Status.PROCESSING,
                    next_retry_at__lte=now,
                )
            )
            .filter(Q(next_retry_at__isnull=True) | Q(next_retry_at__lte=now))
            .order_by("received_at")[:batch_size]
        )
        for event in queryset:
            event.status = WebhookEvent.Status.PROCESSING
            event.next_retry_at = now + timedelta(minutes=reservation_timeout)
            event.save(
                update_fields=["status", "next_retry_at", "updated_at"]
            )
            reserved.append(event.pk)

    published = 0
    for event_id in reserved:
        try:
            process_webhook_event_task.apply_async(
                args=[event_id],
                queue="default",
            )
            published += 1
        except Exception as exc:
            logger.warning(
                "billing_webhook_publish_failed",
                extra={
                    "webhook_event_id": event_id,
                    "exception_type": exc.__class__.__name__,
                },
            )
            WebhookEvent.objects.filter(pk=event_id).update(
                status=WebhookEvent.Status.RETRY,
                next_retry_at=timezone.now() + timedelta(seconds=30),
                last_error="Falha temporária ao publicar o evento.",
                error_message="Falha temporária ao publicar o evento.",
            )
    return published
