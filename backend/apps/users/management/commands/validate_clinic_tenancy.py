"""Valida memberships obrigatórios e clínica ativa das sessões."""

from django.core.management.base import BaseCommand, CommandError

from apps.users.services.clinics import validate_clinic_foundation


class Command(BaseCommand):
    help = "Valida a consistência da fundação multi-tenant por clínica."

    def handle(self, *args, **options):
        del args, options
        result = validate_clinic_foundation()
        self.stdout.write(
            "Validação tenant: "
            f"usuarios_sem_membership={len(result.eligible_users_without_membership)} "
            f"sessoes_invalidas={len(result.sessions_with_invalid_clinic)}"
        )
        if not result.is_valid:
            raise CommandError("A fundação tenant possui registros órfãos ou sessões inválidas.")
        self.stdout.write(self.style.SUCCESS("Fundação tenant válida."))
