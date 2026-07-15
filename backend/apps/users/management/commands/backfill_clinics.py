"""Cria clínicas padrão e memberships para usuários legados elegíveis."""

from django.core.management.base import BaseCommand

from apps.users.services.clinics import backfill_default_clinics


class Command(BaseCommand):
    help = "Executa o backfill idempotente da fundação de clínicas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            action="append",
            dest="user_ids",
            type=int,
            help="Limita o backfill a um ou mais IDs técnicos de usuário.",
        )

    def handle(self, *args, **options):
        del args
        result = backfill_default_clinics(user_ids=options.get("user_ids"))
        self.stdout.write(
            self.style.SUCCESS(
                "Backfill concluído: "
                f"usuarios={result.users_scanned} "
                f"clinicas={result.clinics_created} "
                f"memberships={result.memberships_created} "
                f" sessoes={result.sessions_updated}"
            )
        )
