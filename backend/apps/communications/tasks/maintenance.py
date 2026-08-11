"""Tasks periódicas de limpeza e retenção."""

from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.communications.models import (
    InAppNotification,
    PublicCommunicationActionToken,
)


@shared_task(
    name="apps.communications.tasks.cleanup_expired_public_tokens",
    acks_late=True,
    ignore_result=True,
)
def cleanup_expired_public_tokens() -> int:
    retention_days = max(
        int(getattr(settings, "COMMUNICATIONS_TOKEN_RETENTION_DAYS", 90)),
        1,
    )
    cutoff = timezone.now() - timedelta(days=retention_days)
    deleted, _ = PublicCommunicationActionToken.objects.filter(
        expires_at__lt=cutoff
    ).delete()
    return deleted


@shared_task(
    name="apps.communications.tasks.cleanup_expired_notifications",
    acks_late=True,
    ignore_result=True,
)
def cleanup_expired_notifications() -> int:
    now = timezone.now()
    retention_days = max(
        int(getattr(settings, "NOTIFICATION_RETENTION_DAYS", 180)),
        30,
    )
    cutoff = now - timedelta(days=retention_days)
    queryset = InAppNotification.objects.filter(
        expires_at__lt=now,
        archived_at__isnull=True,
    ) | InAppNotification.objects.filter(archived_at__lt=cutoff)
    return queryset.update(archived_at=now)
