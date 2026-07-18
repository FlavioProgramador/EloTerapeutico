"""Casos de uso transacionais de telemedicina e lembretes."""

from __future__ import annotations

from django.db import transaction

from apps.scheduling.exceptions import TelemedicineUnavailableError
from apps.scheduling.models import AppointmentReminder, TelemedicineRoom


@transaction.atomic
def regenerate_telemedicine_links(*, actor, room: TelemedicineRoom) -> TelemedicineRoom:
    locked = TelemedicineRoom.objects.select_for_update().get(pk=room.pk)
    locked.regenerate_tokens()
    return locked


@transaction.atomic
def open_telemedicine_room(*, actor, room: TelemedicineRoom) -> TelemedicineRoom:
    locked = TelemedicineRoom.objects.select_for_update().get(pk=room.pk)
    if not locked.is_accessible:
        raise TelemedicineUnavailableError("A sala não está disponível.")
    locked.status = TelemedicineRoom.Status.IN_PROGRESS
    locked.save(update_fields=["status", "updated_at"])
    return locked


@transaction.atomic
def cancel_appointment_reminder(
    *,
    actor,
    reminder: AppointmentReminder,
) -> AppointmentReminder:
    locked = AppointmentReminder.objects.select_for_update().get(pk=reminder.pk)
    locked.status = AppointmentReminder.Status.CANCELLED
    locked.save(update_fields=["status", "updated_at"])
    return locked


__all__ = [
    "cancel_appointment_reminder",
    "open_telemedicine_room",
    "regenerate_telemedicine_links",
]
