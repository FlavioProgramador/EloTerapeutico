"""Operações de escrita do ciclo de vida do cadastro."""

from django.db import transaction
from django.utils import timezone

from apps.patients.exceptions import InvalidPatientState


@transaction.atomic
def deactivate(instance):
    if not instance.is_active:
        raise InvalidPatientState("Paciente já está desativado.")
    instance.is_active = False
    instance.status = instance.Status.INACTIVE
    instance.deleted_at = timezone.now()
    instance.save(update_fields=["is_active", "status", "deleted_at", "updated_at"])
    return instance


@transaction.atomic
def restore(instance):
    if instance.is_active:
        raise InvalidPatientState("Paciente já está ativo.")
    instance.restore()
    return instance
