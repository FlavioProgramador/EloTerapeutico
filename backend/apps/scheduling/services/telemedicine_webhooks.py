from __future__ import annotations

import hashlib

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.scheduling.integrations.telemedicine import get_telemedicine_provider
from apps.scheduling.models import (
    TelemedicineParticipantSession,
    TelemedicineRoom,
    TelemedicineWebhookEvent,
)
from apps.scheduling.selectors.telemedicine import get_telemedicine_room_by_provider_name


def _participant_role(identity: str) -> str | None:
    parts = identity.split(":")
    if len(parts) < 4 or parts[0] != "telemed":
        return None
    role = parts[2]
    if role in {
        TelemedicineParticipantSession.Role.PATIENT,
        TelemedicineParticipantSession.Role.PROFESSIONAL,
    }:
        return role
    return None


def _active_roles(room: TelemedicineRoom) -> set[str]:
    return set(
        room.participant_sessions.filter(left_at__isnull=True).values_list(
            "role", flat=True
        )
    )


def _update_room_presence(room: TelemedicineRoom) -> None:
    roles = _active_roles(room)
    if {
        TelemedicineParticipantSession.Role.PATIENT,
        TelemedicineParticipantSession.Role.PROFESSIONAL,
    }.issubset(roles):
        if room.status in {
            TelemedicineRoom.Status.AVAILABLE,
            TelemedicineRoom.Status.WAITING,
        }:
            room.transition_to(TelemedicineRoom.Status.IN_PROGRESS, save=False)
    elif roles and room.status in {
        TelemedicineRoom.Status.AVAILABLE,
        TelemedicineRoom.Status.IN_PROGRESS,
    }:
        room.transition_to(TelemedicineRoom.Status.WAITING, save=False)
    room.save()


def _handle_participant_joined(room: TelemedicineRoom, provider_event) -> None:
    role = _participant_role(provider_event.participant_identity)
    if not role:
        return
    session, created = TelemedicineParticipantSession.objects.get_or_create(
        room=room,
        provider_participant_identity=provider_event.participant_identity,
        defaults={
            "organization": room.organization,
            "role": role,
            "provider_participant_sid": provider_event.participant_sid,
            "joined_at": provider_event.occurred_at or timezone.now(),
        },
    )
    if not created and session.left_at:
        session.left_at = None
        session.disconnect_reason = ""
        session.connection_aborted = False
        session.provider_participant_sid = provider_event.participant_sid
        session.joined_at = provider_event.occurred_at or timezone.now()
        session.save()

    joined_at = provider_event.occurred_at or timezone.now()
    if role == TelemedicineParticipantSession.Role.PATIENT:
        room.patient_joined_at = room.patient_joined_at or joined_at
    else:
        room.professional_joined_at = room.professional_joined_at or joined_at
    _update_room_presence(room)


def _handle_participant_left(
    room: TelemedicineRoom,
    provider_event,
    *,
    connection_aborted: bool,
) -> None:
    session = (
        room.participant_sessions.filter(
            provider_participant_identity=provider_event.participant_identity,
            left_at__isnull=True,
        )
        .order_by("-joined_at")
        .first()
    )
    if session:
        session.left_at = provider_event.occurred_at or timezone.now()
        session.disconnect_reason = provider_event.disconnect_reason[:64]
        session.connection_aborted = connection_aborted
        session.save(
            update_fields=[
                "left_at",
                "disconnect_reason",
                "connection_aborted",
                "updated_at",
            ]
        )
    room.last_participant_left_at = provider_event.occurred_at or timezone.now()
    _update_room_presence(room)


@transaction.atomic
def process_telemedicine_webhook(
    *,
    raw_body: str,
    authorization: str,
) -> tuple[TelemedicineWebhookEvent, bool]:
    provider = get_telemedicine_provider()
    provider_event = provider.parse_webhook(
        body=raw_body,
        authorization=authorization,
    )
    payload_hash = hashlib.sha256(raw_body.encode()).hexdigest()

    try:
        event, created = TelemedicineWebhookEvent.objects.get_or_create(
            provider="livekit",
            provider_event_id=provider_event.event_id,
            defaults={
                "event_type": provider_event.event_type,
                "occurred_at": provider_event.occurred_at,
                "payload_hash": payload_hash,
            },
        )
    except IntegrityError:
        event = TelemedicineWebhookEvent.objects.get(
            provider="livekit",
            provider_event_id=provider_event.event_id,
        )
        return event, False

    if not created or event.processed_at:
        return event, False

    room = get_telemedicine_room_by_provider_name(
        room_name=provider_event.room_name
    )
    event.room = room
    if room is None:
        event.processing_error = "Sala não encontrada."
        event.processed_at = timezone.now()
        event.save(
            update_fields=["room", "processing_error", "processed_at"]
        )
        return event, True

    room = TelemedicineRoom.objects.select_for_update().get(pk=room.pk)
    if provider_event.room_sid and not room.provider_room_sid:
        room.provider_room_sid = provider_event.room_sid

    event_type = provider_event.event_type
    if event_type == "room_started":
        if room.status == TelemedicineRoom.Status.PENDING:
            room.transition_to(TelemedicineRoom.Status.AVAILABLE, save=False)
        room.save()
    elif event_type == "participant_joined":
        _handle_participant_joined(room, provider_event)
    elif event_type == "participant_left":
        _handle_participant_left(
            room,
            provider_event,
            connection_aborted=False,
        )
    elif event_type == "participant_connection_aborted":
        _handle_participant_left(
            room,
            provider_event,
            connection_aborted=True,
        )
    elif event_type == "room_finished":
        if room.status not in room.TERMINAL_STATUSES:
            room.transition_to(TelemedicineRoom.Status.FINISHED, save=False)
        room.revoked_at = room.revoked_at or timezone.now()
        room.save()
        room.invitations.filter(revoked_at__isnull=True).update(
            revoked_at=timezone.now(),
            updated_at=timezone.now(),
        )

    event.processed_at = timezone.now()
    event.save(update_fields=["room", "processed_at"])
    return event, True
