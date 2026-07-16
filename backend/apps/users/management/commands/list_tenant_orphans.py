"""Lista somente identificadores técnicos de inconsistências tenant."""

import json

from django.core.management.base import BaseCommand

from apps.users.services.clinics import validate_clinic_foundation


class Command(BaseCommand):
    help = "Lista IDs técnicos de usuários e sessões com inconsistência tenant."

    def handle(self, *args, **options):
        del args, options
        result = validate_clinic_foundation()
        payload = {
            "eligible_user_ids_without_membership": list(
                result.eligible_users_without_membership
            ),
            "session_ids_with_invalid_clinic": list(
                result.sessions_with_invalid_clinic
            ),
        }
        self.stdout.write(json.dumps(payload, sort_keys=True))
