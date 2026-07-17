from __future__ import annotations

from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from apps.billing.models import WebhookEvent
from apps.billing.security import redact_sensitive_data


def persist_webhook_event(
    *,
    payload: dict,
    event_type: str,
    event_hash: str,
    event_identifier: str | None,
) -> WebhookEvent:
    defaults = {
        "gateway_name": "ASAAS",
        "event_type": event_type,
        "payload": redact_sensitive_data(payload),
        "status": WebhookEvent.Status.RECEIVED,
    }
    if event_identifier:
        lookup = {"event_id": event_identifier}
        defaults["payload_hash"] = event_hash
    else:
        lookup = {"payload_hash": event_hash}
        defaults["event_id"] = None

    try:
        with transaction.atomic():
            webhook_event, _ = WebhookEvent.objects.get_or_create(
                **lookup,
                defaults=defaults,
            )
            return webhook_event
    except IntegrityError:
        query = Q(payload_hash=event_hash)
        if event_identifier:
            query |= Q(event_id=event_identifier)
        return WebhookEvent.objects.get(query)


def finish_event(
    event_id: int,
    result: str,
    max_retries: int,
) -> WebhookEvent:
    with transaction.atomic():
        locked = WebhookEvent.objects.select_for_update().get(pk=event_id)
        if result.startswith("retry:"):
            locked.status = (
                WebhookEvent.Status.FAILED
                if locked.attempt_count >= max_retries
                else WebhookEvent.Status.RETRY
            )
            locked.next_retry_at = (
                None
                if locked.status == WebhookEvent.Status.FAILED
                else timezone.now()
                + timedelta(minutes=min(2**locked.attempt_count, 60))
            )
            locked.last_error = result.removeprefix("retry: ")
            locked.error_message = locked.last_error
            locked.processed = False
            locked.processed_at = None
        elif result.startswith("ignored:"):
            locked.status = WebhookEvent.Status.IGNORED
            locked.last_error = result.removeprefix("ignored: ")
            locked.error_message = locked.last_error
            locked.processed = True
            locked.processed_at = timezone.now()
            locked.next_retry_at = None
        else:
            locked.status = WebhookEvent.Status.PROCESSED
            locked.last_error = ""
            locked.error_message = ""
            locked.processed = True
            locked.processed_at = timezone.now()
            locked.next_retry_at = None
        locked.save(
            update_fields=[
                "status",
                "next_retry_at",
                "last_error",
                "error_message",
                "processed",
                "processed_at",
                "updated_at",
            ]
        )
        return locked
