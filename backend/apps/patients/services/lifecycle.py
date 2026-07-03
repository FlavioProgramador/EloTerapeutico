"""Operações de escrita do ciclo de vida do cadastro."""

from django.db import transaction

from ..exceptions import InvalidPatientState


@transaction.atomic
def deactivate(instance):
    if not instance.is_active:
        raise InvalidPatientState("Paciente já está desativado.")
    instance.deactivate()
    return instance


@transaction.atomic
def restore(instance):
    if instance.is_active:
        raise InvalidPatientState("Paciente já está ativo.")
    instance.restore()
    return instance
