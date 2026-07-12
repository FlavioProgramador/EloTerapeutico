from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.billing.services.trials import expire_finished_trials


class Command(BaseCommand):
    help = "Expira testes gratuitos finalizados sem apagar dados das contas."

    def handle(self, *args, **options):
        expired = expire_finished_trials(at=timezone.now())
        self.stdout.write(
            self.style.SUCCESS(f"{expired} teste(s) gratuito(s) expirado(s).")
        )
