from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.scheduling.integrations.telemedicine import (
    TelemedicineProviderError,
    get_telemedicine_provider,
)
from apps.scheduling.models import Appointment, TelemedicineRoom
from apps.scheduling.models.remote import generate_provider_room_name
from apps.scheduling.telemedicine_config import get_telemedicine_config


def _close_provider_room_safely(room_name: str) -> None:
    config = get_telemedicine_config()
    if not config.provider_configured:
        return
    try:
        get_telemedicine_provider().close_room(room_name=room_name)
    except TelemedicineProviderError:
        return


@transaction.atomic
def sync_telemedicine_for_appointment(
    *,
    appointment: Appointment,
    actor=None,
) -> TelemedicineRoom | None:
    """Mantém uma única sala coerente com modalidade, horário e status."""

    appointment = Appointment.objects.select_related("organization").get(
        pk=appointment.pk
    )
    online = appointment.modality in {
        Appointment.Modality.ONLINE,
        Appointment.Modality.HYBRID,
    }
    active = appointment.status in {
        Appointment.Status.SCHEDULED,
        Appointment.Status.CONFIRMED,
        Appointment.Status.RESCHEDULED,
    }
    room = (
        TelemedicineRoom.objects.select_for_update()
        .filter(appointment=appointment)
        .first()
    )

    if online and active:
        expires_at = appointment.end_time + timedelta(hours=2)
        if room is None:
            return TelemedicineRoom.objects.create(
                organization=appointment.organization,
                appointment=appointment,
                expires_at=expires_at,
                status=TelemedicineRoom.Status.AVAILABLE,
                e2ee_enabled=True,
            )

        room.expires_at = expires_at
        if room.status in room.TERMINAL_STATUSES or room.revoked_at:
            now = timezone.now()
            room.invitations.filter(revoked_at__isnull=True).update(
                revoked_at=now,
                updated_at=now,
            )
            old_provider_room = room.provider_room_name
            room.provider_room_name = generate_provider_room_name()
            room.provider_room_sid = ""
            room.e2ee_key = ""
            room.status = TelemedicineRoom.Status.AVAILABLE
            room.revoked_at = None
            room.started_at = None
            room.ended_at = None
            room.patient_joined_at = None
            room.professional_joined_at = None
            room.last_participant_left_at = None
            room.closed_by = None
            room.failure_code = ""
            transaction.on_commit(
                lambda room_name=old_provider_room: _close_provider_room_safely(
                    room_name
                )
            )
        room.save()
        return room

    if room is None or room.status in room.TERMINAL_STATUSES:
        return room

    target_status = (
        TelemedicineRoom.Status.FINISHED
        if appointment.status == Appointment.Status.COMPLETED
        else TelemedicineRoom.Status.CANCELLED
    )
    provider_room_name = room.provider_room_name
    room.revoke(actor=actor, status=target_status)
    transaction.on_commit(
        lambda room_name=provider_room_name: _close_provider_room_safely(room_name)
    )
    return room
