from __future__ import annotations

import logging
import os

from django.conf import settings
from django.db import transaction

from apps.billing.infrastructure.payments.asaas.client import AsaasGateway
from apps.billing.models import WebhookEvent

from .identifiers import event_id, payload_hash
from .payments import process_payment_event
from .persistence import finish_event, persist_webhook_event
from .subscriptions import process_subscription_event

logger = logging.getLogger(__name__)


def hydrate_payment_for_worker(payload: dict) -> dict:
    payment_data = dict(payload.get("payment") or {})
    payment_id = payment_data.get("id")
    if not payment_id:
        return payment_data
    gateway_payload = AsaasGateway().get_payment(payment_id)
    return {**payment_data, **gateway_payload, "id": payment_id}


def process_webhook_event(
    event: WebhookEvent,
    *,
    payload_override: dict | None = None,
) -> WebhookEvent:
    max_retries = max(
        int(getattr(settings, "BILLING_WEBHOOK_MAX_RETRIES", 5)),
        1,
    )
    with transaction.atomic():
        locked = WebhookEvent.objects.select_for_update().get(pk=event.pk)
        if locked.status in {
            WebhookEvent.Status.PROCESSED,
            WebhookEvent.Status.IGNORED,
        }:
            return locked
        locked.status = WebhookEvent.Status.PROCESSING
        locked.attempt_count += 1
        locked.save(
            update_fields=["status", "attempt_count", "updated_at"]
        )

    try:
        with transaction.atomic():
            payload = payload_override or event.payload
            event_type = event.event_type
            if event_type.startswith("PAYMENT_"):
                payment_data = (
                    payload.get("payment") or {}
                    if payload_override is not None
                    else hydrate_payment_for_worker(payload)
                )
                result = process_payment_event(event_type, payment_data)
            elif event_type.startswith("SUBSCRIPTION_"):
                result = process_subscription_event(
                    event_type,
                    payload.get("subscription") or {},
                )
            else:
                result = f"ignored: evento não mapeado ({event_type})"
        return finish_event(event.pk, result, max_retries)
    except Exception as exc:
        logger.exception(
            "asaas_webhook_processing_error",
            extra={
                "event_type": event.event_type,
                "exception_type": exc.__class__.__name__,
            },
        )
        return finish_event(
            event.pk,
            "retry: Falha interna ao processar o evento.",
            max_retries,
        )


def process_inline_enabled() -> bool:
    configured = getattr(settings, "BILLING_WEBHOOK_PROCESS_INLINE", None)
    if configured is not None:
        return bool(configured)
    return os.getenv(
        "BILLING_WEBHOOK_PROCESS_INLINE",
        "false",
    ).strip().lower() in {"1", "true", "yes", "on"}


def handle_asaas_webhook(request) -> WebhookEvent:
    payload = AsaasGateway(require_api_key=False).parse_webhook(request)
    event_type = payload.get("event", "UNKNOWN")
    webhook_event = persist_webhook_event(
        payload=payload,
        event_type=event_type,
        event_hash=payload_hash(payload),
        event_identifier=event_id(payload),
    )
    if process_inline_enabled():
        return process_webhook_event(
            webhook_event,
            payload_override=payload,
        )
    return webhook_event
