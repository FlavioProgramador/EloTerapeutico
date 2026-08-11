from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.communications.models import Communication, CommunicationAttempt


class Command(BaseCommand):
    help = "Libera comunicações cuja falha temporária atingiu o horário de nova tentativa."

    def handle(self, *args, **options):
        now = timezone.now()
        communication_ids = CommunicationAttempt.objects.filter(status=CommunicationAttempt.Status.RETRYABLE_FAILURE, next_retry_at__lte=now, communication__status=Communication.Status.QUEUED).values_list("communication_id", flat=True)
        updated = Communication.objects.filter(id__in=communication_ids).update(queued_at=now, next_retry_at=None)
        self.stdout.write(self.style.SUCCESS(f"Comunicações liberadas para retentativa: {updated}"))
