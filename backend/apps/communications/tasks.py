"""Tarefas Celery de comunicações e automações."""

from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.communications.models import (
    Communication,
    InAppNotification,
    NotificationDelivery,
    PublicCommunicationActionToken,
)
from apps.communications.services.dispatch import claim_due_communications, dispatch_communication
from apps.communications.services.scheduled_operations import schedule_operational_automations


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
            "status": Communication.Status.FAILED if final else Communication.Status.QUEUED,
            "processing_started_at": None,
            "next_retry_at": None if final else timezone.now() + timedelta(seconds=countdown),
        }
        if final:
            updates["failed_at"] = timezone.now()
        Communication.objects.filter(
            pk=communication_id,
            status=Communication.Status.PROCESSING,
        ).update(**updates)
        if final:
            raise
        raise self.retry(exc=exc, countdown=countdown, max_retries=self.max_retries)


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
            send_communication.apply_async(args=[communication_id], queue="communications")
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


@shared_task(
    name="apps.communications.tasks.schedule_operational_automations",
    acks_late=True,
    ignore_result=True,
    soft_time_limit=180,
    time_limit=240,
)
def schedule_operational_automations_task() -> dict[str, int]:
    return schedule_operational_automations(
        due_days=max(int(getattr(settings, "COMMUNICATIONS_PAYMENT_DUE_DAYS", 3)), 0),
        form_reminder_hours=max(int(getattr(settings, "COMMUNICATIONS_FORM_REMINDER_HOURS", 24)), 1),
        document_reminder_hours=max(
            int(getattr(settings, "COMMUNICATIONS_DOCUMENT_REMINDER_HOURS", 24)),
            1,
        ),
    )


@shared_task(
    name="apps.communications.tasks.cleanup_expired_public_tokens",
    acks_late=True,
    ignore_result=True,
)
def cleanup_expired_public_tokens() -> int:
    retention_days = max(int(getattr(settings, "COMMUNICATIONS_TOKEN_RETENTION_DAYS", 90)), 1)
    cutoff = timezone.now() - timedelta(days=retention_days)
    deleted, _ = PublicCommunicationActionToken.objects.filter(expires_at__lt=cutoff).delete()
    return deleted


@shared_task(
    bind=True,
    name="apps.communications.tasks.send_notification_delivery",
    acks_late=True,
    reject_on_worker_lost=True,
    max_retries=4,
    soft_time_limit=60,
    time_limit=90,
)
def send_notification_delivery(self, delivery_id: int) -> None:
    delivery = NotificationDelivery.objects.select_related("notification__recipient").filter(pk=delivery_id).first()
    if delivery is None or delivery.status in {NotificationDelivery.Status.SENT, NotificationDelivery.Status.DELIVERED, NotificationDelivery.Status.SKIPPED}:
        return
    delivery.status = NotificationDelivery.Status.PROCESSING
    delivery.attempt_count += 1
    delivery.last_error = ""
    delivery.save(update_fields=["status", "attempt_count", "last_error", "updated_at"])
    notification = delivery.notification
    try:
        if delivery.channel != NotificationDelivery.Channel.EMAIL:
            delivery.status = NotificationDelivery.Status.SKIPPED
            delivery.last_error = "Canal ainda não configurado."
        elif not notification.recipient.email:
            delivery.status = NotificationDelivery.Status.SKIPPED
            delivery.last_error = "Destinatário sem e-mail cadastrado."
        else:
            sent = send_mail(
                subject=notification.title,
                message=f"{notification.message}\n\nAcesse o Elo Terapêutico para revisar.",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[notification.recipient.email],
                fail_silently=False,
            )
            if sent != 1:
                raise RuntimeError("backend_email_not_confirmed")
            delivery.status = NotificationDelivery.Status.SENT
            delivery.sent_at = timezone.now()
            delivery.provider = "django_email"
            delivery.last_error = ""
        delivery.next_retry_at = None
        delivery.save(update_fields=["status", "attempt_count", "provider", "sent_at", "next_retry_at", "last_error", "updated_at"])
    except Exception as exc:
        countdown = min(60 * (2 ** self.request.retries), 3600)
        final = self.request.retries >= self.max_retries
        delivery.status = NotificationDelivery.Status.FAILED if final else NotificationDelivery.Status.PENDING
        delivery.failed_at = timezone.now() if final else None
        delivery.next_retry_at = None if final else timezone.now() + timedelta(seconds=countdown)
        delivery.last_error = "Falha temporária no envio da notificação."
        delivery.save(update_fields=["status", "attempt_count", "failed_at", "next_retry_at", "last_error", "updated_at"])
        if not final:
            raise self.retry(exc=exc, countdown=countdown)
        raise


@shared_task(
    name="apps.communications.tasks.cleanup_expired_notifications",
    acks_late=True,
    ignore_result=True,
)
def cleanup_expired_notifications() -> int:
    now = timezone.now()
    retention_days = max(int(getattr(settings, "NOTIFICATION_RETENTION_DAYS", 180)), 30)
    cutoff = now - timedelta(days=retention_days)
    queryset = InAppNotification.objects.filter(
        expires_at__lt=now,
        archived_at__isnull=True,
    ) | InAppNotification.objects.filter(
        archived_at__lt=cutoff,
    )
    updated = queryset.update(archived_at=now)
    return updated
