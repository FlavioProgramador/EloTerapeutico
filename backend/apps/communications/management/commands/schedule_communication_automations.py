from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.communications.services.scheduled_operations import schedule_operational_automations


class Command(BaseCommand):
    help = "Agenda automações operacionais de forma idempotente."

    def add_arguments(self, parser):
        parser.add_argument("--due-days", type=int, default=3)
        parser.add_argument("--form-reminder-hours", type=int, default=24)
        parser.add_argument("--document-reminder-hours", type=int, default=24)

    def handle(self, *args, **options):
        counters = schedule_operational_automations(
            due_days=options["due_days"],
            form_reminder_hours=options["form_reminder_hours"],
            document_reminder_hours=options["document_reminder_hours"],
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Automações agendadas: "
                f"financeiro={counters['finance']}, "
                f"formulários={counters['forms']}, "
                f"documentos={counters['documents']}, "
                f"pacotes={counters['packages']}"
            )
        )
