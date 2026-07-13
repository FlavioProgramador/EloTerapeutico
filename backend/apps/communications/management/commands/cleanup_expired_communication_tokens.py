from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.communications.models import PublicCommunicationActionToken


class Command(BaseCommand):
    help = "Remove tokens públicos expirados fora da janela de retenção operacional."

    def add_arguments(self, parser):
        parser.add_argument("--retention-days", type=int, default=90)

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=max(options["retention_days"], 1))
        deleted, _ = PublicCommunicationActionToken.objects.filter(expires_at__lt=cutoff).delete()
        self.stdout.write(self.style.SUCCESS(f"Tokens removidos: {deleted}"))
