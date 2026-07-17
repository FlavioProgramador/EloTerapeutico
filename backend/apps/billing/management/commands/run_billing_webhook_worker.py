import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.billing.integrations.asaas.webhooks import process_webhook_event
from apps.billing.models import WebhookEvent


class Command(BaseCommand):
    help = (
        "Processa eventos de webhook de billing persistidos, "
        "com retry e lock transacional."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Processa a fila atual e encerra.",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=2.0,
            help="Intervalo entre consultas da fila.",
        )

    def handle(self, *args, **options):
        run_once = options["once"]
        sleep_seconds = max(options["sleep"], 0.2)
        processed = 0

        while True:
            event_id = self._claim_next_event()
            if event_id is None:
                if run_once:
                    break
                time.sleep(sleep_seconds)
                continue

            event = WebhookEvent.objects.get(pk=event_id)
            process_webhook_event(event)
            processed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Eventos processados nesta execução: {processed}"
            )
        )

    @staticmethod
    def _claim_next_event():
        now = timezone.now()
        with transaction.atomic():
            event = (
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
                .filter(
                    Q(next_retry_at__isnull=True)
                    | Q(next_retry_at__lte=now)
                )
                .order_by("received_at")
                .first()
            )
            if not event:
                return None
            event.status = WebhookEvent.Status.PROCESSING
            event.next_retry_at = now + timedelta(minutes=5)
            event.save(
                update_fields=["status", "next_retry_at", "updated_at"]
            )
            return event.pk
