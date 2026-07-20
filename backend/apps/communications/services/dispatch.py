from __future__ import annotations

import logging
import time
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from ..constants import RETRY_DELAYS_SECONDS
from ..integrations.providers import (
    InvalidRecipient,
    PermanentProviderError,
    ProviderError,
    ProviderNotConfigured,
    RetryableProviderError,
    get_provider,
)
from ..models import (
    Communication,
    CommunicationAttempt,
    CommunicationChannelConfig,
    CommunicationRecipient,
)

logger = logging.getLogger(__name__)


def claim_due_communications(*, batch_size: int | None = None) -> list[int]:
    now = timezone.now()
    size = batch_size or getattr(settings, "COMMUNICATIONS_BATCH_SIZE", 50)
    processing_timeout = timedelta(
        minutes=getattr(
            settings,
            "COMMUNICATIONS_PROCESSING_TIMEOUT_MINUTES",
            15,
        )
    )
    with transaction.atomic():
        Communication.objects.filter(
            status=Communication.Status.PROCESSING,
            processing_started_at__lt=now - processing_timeout,
        ).update(
            status=Communication.Status.QUEUED,
            processing_started_at=None,
        )
        queryset = (
            Communication.objects.select_for_update(skip_locked=True)
            .filter(
                (
                    Q(status=Communication.Status.QUEUED)
                    & (
                        Q(next_retry_at__isnull=True)
                        | Q(next_retry_at__lte=now)
                    )
                )
                | Q(
                    status=Communication.Status.SCHEDULED,
                    scheduled_at__lte=now,
                ),
                archived_at__isnull=True,
            )
            .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
            .order_by("priority", "scheduled_at", "created_at")[:size]
        )
        ids = list(queryset.values_list("id", flat=True))
        Communication.objects.filter(id__in=ids).update(
            status=Communication.Status.PROCESSING,
            processing_started_at=now,
        )
    return ids


def _next_attempt_number(communication, recipient) -> int:
    last = (
        CommunicationAttempt.objects.filter(
            communication=communication,
            recipient=recipient,
        )
        .order_by("-attempt_number")
        .values_list("attempt_number", flat=True)
        .first()
    )
    return (last or 0) + 1


def _sanitize_error(exc: Exception) -> str:
    return exc.__class__.__name__[:80]


def dispatch_communication(communication_id: int) -> Communication:
    communication = Communication.objects.select_related("owner", "patient").get(
        pk=communication_id
    )
    if communication.status != Communication.Status.PROCESSING:
        return communication
    if communication.expires_at and communication.expires_at <= timezone.now():
        communication.status = Communication.Status.EXPIRED
        communication.save(update_fields=["status", "updated_at"])
        return communication

    channel_config = CommunicationChannelConfig.objects.filter(
        owner=communication.owner,
        channel=communication.channel,
    ).first()
    provider = get_provider(communication.channel, config=channel_config)
    recipients = list(communication.recipients.all())
    if not recipients:
        communication.status = Communication.Status.FAILED
        communication.failed_at = timezone.now()
        communication.save(
            update_fields=["status", "failed_at", "updated_at"]
        )
        return communication

    final_status: str = str(Communication.Status.SENT)
    any_retry = False
    for recipient in recipients:
        attempt_number = _next_attempt_number(communication, recipient)
        attempt = CommunicationAttempt.objects.create(
            communication=communication,
            recipient=recipient,
            attempt_number=attempt_number,
            provider=provider.name,
            status=CommunicationAttempt.Status.PROCESSING,
            started_at=timezone.now(),
        )
        started = time.monotonic()
        try:
            result = provider.send(communication, recipient)
        except (
            ProviderNotConfigured,
            InvalidRecipient,
            PermanentProviderError,
        ) as exc:
            attempt.status = CommunicationAttempt.Status.PERMANENT_FAILURE
            attempt.error_code = _sanitize_error(exc)
            attempt.error_message = (
                "Falha permanente ao processar o canal ou destinatário."
            )
            recipient.status = CommunicationRecipient.Status.FAILED
            final_status = Communication.Status.FAILED
        except (RetryableProviderError, ProviderError) as exc:
            max_attempts = getattr(settings, "COMMUNICATIONS_MAX_ATTEMPTS", 5)
            if attempt_number >= max_attempts:
                attempt.status = CommunicationAttempt.Status.PERMANENT_FAILURE
                attempt.error_message = "Número máximo de tentativas atingido."
                final_status = Communication.Status.FAILED
            else:
                attempt.status = CommunicationAttempt.Status.RETRYABLE_FAILURE
                delay_index = min(
                    attempt_number - 1,
                    len(RETRY_DELAYS_SECONDS) - 1,
                )
                attempt.next_retry_at = timezone.now() + timedelta(
                    seconds=RETRY_DELAYS_SECONDS[delay_index]
                )
                communication.next_retry_at = attempt.next_retry_at
                attempt.error_message = (
                    "Falha temporária; uma nova tentativa foi agendada."
                )
                final_status = Communication.Status.QUEUED
                any_retry = True
            attempt.error_code = _sanitize_error(exc)
        else:
            attempt.status = CommunicationAttempt.Status.SUCCESS
            attempt.external_id = result.provider_message_id[:160]
            attempt.metadata = {
                key: value
                for key, value in result.metadata.items()
                if key
                in {
                    "manual_url",
                    "requires_confirmation",
                    "provider_status",
                    "price",
                    "price_unit",
                }
            }
            recipient.status = (
                CommunicationRecipient.Status.READY
                if communication.channel == Communication.Channel.WHATSAPP_MANUAL
                else CommunicationRecipient.Status.SENT
            )
            final_status = str(result.status)
            communication.provider_name = provider.name
            communication.provider_message_id = result.provider_message_id[:160]
            if result.metadata:
                communication.metadata = {
                    **communication.metadata,
                    **attempt.metadata,
                }
        finally:
            attempt.finished_at = timezone.now()
            attempt.latency_ms = int((time.monotonic() - started) * 1000)
            attempt.save()
            recipient.save(update_fields=["status", "updated_at"])

    now = timezone.now()
    communication.status = final_status
    communication.processing_started_at = None
    if final_status != Communication.Status.QUEUED:
        communication.next_retry_at = None
    if final_status in {
        Communication.Status.SENT,
        Communication.Status.DELIVERED,
    }:
        communication.sent_at = now
        if final_status == Communication.Status.DELIVERED:
            communication.delivered_at = now
    elif final_status == Communication.Status.FAILED:
        communication.failed_at = now
        from .notifications import create_notification

        create_notification(
            owner=communication.owner,
            recipient=communication.owner,
            communication=communication,
            title="Falha no envio de comunicação",
            message=(
                "Não foi possível enviar uma comunicação. "
                "Revise o canal e tente novamente."
            ),
            event_type="communications.failed",
            category="communications",
            priority="high",
            internal_url=f"/dashboard/comunicacoes/{communication.public_id}",
            action_label="Revisar comunicação",
            deduplication_key=f"communication-failed:{communication.pk}",
        )
    elif any_retry:
        communication.queued_at = now
    communication.save()
    logger.info(
        "communication_dispatch_completed",
        extra={
            "communication_id": communication.pk,
            "channel": communication.channel,
            "provider": provider.name,
            "status": final_status,
        },
    )
    return communication


def process_due_communications(*, batch_size: int | None = None) -> dict[str, int]:
    ids = claim_due_communications(batch_size=batch_size)
    processed = failed = 0
    for communication_id in ids:
        try:
            communication = dispatch_communication(communication_id)
            processed += 1
            if communication.status == Communication.Status.FAILED:
                failed += 1
        except Exception as exc:
            failed += 1
            Communication.objects.filter(pk=communication_id).update(
                status=Communication.Status.QUEUED,
                processing_started_at=None,
                next_retry_at=timezone.now() + timedelta(minutes=1),
            )
            logger.error(
                "communication_dispatch_unexpected_error",
                extra={
                    "communication_id": communication_id,
                    "exception_type": exc.__class__.__name__,
                },
            )
    return {
        "claimed": len(ids),
        "processed": processed,
        "failed": failed,
    }
