"""Fachada pública dos casos de uso de telemedicina e lembretes."""

from __future__ import annotations

from django.db import transaction

from apps.scheduling.models import AppointmentReminder, TelemedicineRoom
from apps.scheduling.services.telemedicine_access import (
    create_patient_invitation,
    exchange_patient_invitation,
    issue_patient_join_credentials,
    issue_professional_join_credentials,
    record_telemedicine_consent,
    revoke_patient_invitation,
)
from apps.scheduling.services.telemedicine_rooms import (
    expire_telemedicine_rooms,
    finish_telemedicine_room,
    open_telemedicine_room,
    remove_telemedicine_participant,
)
from apps.scheduling.services.telemedicine_webhooks import (
    process_telemedicine_webhook,
)


@transaction.atomic
def regenerate_telemedicine_links(
    *,
    actor,
    room: TelemedicineRoom,
) -> TelemedicineRoom:
    """Compatibilidade: gera somente um novo convite público do paciente."""

    _invitation, _raw_token, invitation_url = create_patient_invitation(
        actor=actor,
        room=room,
    )
    room.generated_patient_link = invitation_url
    return room


@transaction.atomic
def cancel_appointment_reminder(
    *,
    actor,
    reminder: AppointmentReminder,
) -> AppointmentReminder:
    del actor
    locked = AppointmentReminder.objects.select_for_update().get(pk=reminder.pk)
    locked.status = AppointmentReminder.Status.CANCELLED
    locked.save(update_fields=["status", "updated_at"])
    return locked


__all__ = [
    "cancel_appointment_reminder",
    "create_patient_invitation",
    "exchange_patient_invitation",
    "expire_telemedicine_rooms",
    "finish_telemedicine_room",
    "issue_patient_join_credentials",
    "issue_professional_join_credentials",
    "open_telemedicine_room",
    "process_telemedicine_webhook",
    "record_telemedicine_consent",
    "regenerate_telemedicine_links",
    "remove_telemedicine_participant",
    "revoke_patient_invitation",
]
