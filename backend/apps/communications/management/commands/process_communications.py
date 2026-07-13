import time

from django.core.management.base import BaseCommand

from apps.communications.services import process_due_communications


class Command(BaseCommand):
    help = "Processa comunicações agendadas ou enfileiradas usando a fila persistente do banco."

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=None)
        parser.add_argument("--once", action="store_true", help="Executa apenas um lote.")
        parser.add_argument("--sleep", type=int, default=5, help="Intervalo entre lotes em segundos.")

    def handle(self, *args, **options):
        while True:
            result = process_due_communications(batch_size=options["batch_size"])
            self.stdout.write(self.style.SUCCESS(f"Reivindicadas={result['claimed']} processadas={result['processed']} falhas={result['failed']}"))
            if options["once"]:
                break
            time.sleep(max(options["sleep"], 1))
