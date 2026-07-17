"""Tasks de entrega multicanal de notificações."""

from __future__ import annotations

from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.communications.models import NotificationDelivery


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
    delivery = (
        NotificationDelivery.objects.select_related("notification__recipient")
        .filter(pk=delivery_id)
        .first()
    )
    terminal_statuses = {
        NotificationDelivery.Status.SENT,
        NotificationDelivery.Status.DELIVERED,
        NotificationDelivery.Status.SKIPPED,
    }
    if delivery is None or delivery.status in terminal_statuses:
        return

    delivery.status = NotificationDelivery.Status.PROCESSING
    delivery.attempt_count += 1
    delivery.last_error = ""
    delivery.save(
        update_fields=["status", "attempt_count", "last_error", "updated_at"]
    )
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
                message=(
                    f"{notification.message}\n\n"
                    "Acesse o Elo Terapêutico para revisar."
                ),
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
        delivery.save(
            update_fields=[
                "status",
                "attempt_count",
                "provider",
                "sent_at",
                "next_retry_at",
                "last_error",
                "updated_at",
            ]
        )
    except Exception as exc:
        countdown = min(60 * (2**self.request.retries), 3600)
        final = self.request.retries >= self.max_retries
        delivery.status = (
            NotificationDelivery.Status.FAILED
            if final
            else NotificationDelivery.Status.PENDING
        )
        delivery.failed_at = timezone.now() if final else None
        delivery.next_retry_at = (
            None
            if final
            else timezone.now() + timedelta(seconds=countdown)
        )
        delivery.last_error = "Falha temporária no envio da notificação."
        delivery.save(
            update_fields=[
                "status",
                "attempt_count",
                "failed_at",
                "next_retry_at",
                "last_error",
                "updated_at",
            ]
        )
        if not final:
            raise self.retry(exc=exc, countdown=countdown)
        raise
