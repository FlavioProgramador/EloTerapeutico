from __future__ import annotations

import logging
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.communications.models import Communication, CommunicationTemplate
from apps.communications.services import create_communication
from apps.scheduling.models import Appointment, TelemedicineInvitation, TelemedicineRoom
from apps.scheduling.services.telemedicine_access import create_patient_invitation
from apps.scheduling.services.telemedicine_rooms import validate_professional_access

logger = logging.getLogger(__name__)

ALLOWED_INVITATION_CHANNELS = {
    Communication.Channel.EMAIL,
    Communication.Channel.WHATSAPP_MANUAL,
}
TELEMEDICINE_REMINDER_HOURS = 2


def _system_template(*, slug: str, channel: str) -> CommunicationTemplate:
    template = CommunicationTemplate.objects.filter(
        organization__isnull=True,
        owner__isnull=True,
        is_system_template=True,
        is_active=True,
        is_archived=False,
        slug=slug,
        channel=channel,
    ).first()
    if template is None:
        raise ValidationError(
            "O modelo de comunicação online ainda não está disponível."
        )
    return template


def _create_telemedicine_communication(
    *,
    actor,
    room: TelemedicineRoom,
    channel: str,
    template_slug: str,
    source_event: str,
    idempotency_key: str,
    invitation_url: str = "",
    scheduled_at=None,
) -> Communication:
    appointment = room.appointment
    template = _system_template(slug=template_slug, channel=channel)
    return create_communication(
        owner=appointment.therapist,
        created_by=actor,
        organization=room.organization,
        patient=appointment.patient,
        appointment=appointment,
        channel=channel,
        category=template.category,
        template=template,
        variables={"meeting_link": invitation_url},
        scheduled_at=scheduled_at,
        idempotency_key=idempotency_key,
        source_event=source_event,
        source_object_type="TelemedicineRoom",
        source_object_id=str(room.public_id),
        metadata={"event_version": "1"},
    )


def _schedule_telemedicine_reminder(
    *,
    actor,
    room: TelemedicineRoom,
    channel: str,
    invitation: TelemedicineInvitation,
    invitation_url: str,
) -> Communication | None:
    scheduled_at = room.appointment.start_time - timedelta(
        hours=TELEMEDICINE_REMINDER_HOURS
    )
    if scheduled_at <= timezone.now():
        return None
    return _create_telemedicine_communication(
        actor=actor,
        room=room,
        channel=channel,
        template_slug="telemedicine-reminder",
        source_event="telemedicine.invitation.reminder",
        idempotency_key=(
            f"telemedicine-reminder:{invitation.pk}:{channel}:"
            f"{scheduled_at.isoformat()}"
        ),
        invitation_url=invitation_url,
        scheduled_at=scheduled_at,
    )


@transaction.atomic
def send_telemedicine_invitation(
    *,
    actor,
    room: TelemedicineRoom,
    channel: str = Communication.Channel.EMAIL,
) -> Communication:
    """Gera convite, enfileira o envio e agenda um lembrete quando aplicável."""

    if channel not in ALLOWED_INVITATION_CHANNELS:
        raise ValidationError(
            {"channel": "Canal indisponível para convites de atendimento online."}
        )
    validate_professional_access(actor=actor, room=room)
    had_active_invitation = room.invitations.filter(
        role=TelemedicineInvitation.Role.PATIENT,
        revoked_at__isnull=True,
    ).exists()
    invitation, _raw_token, invitation_url = create_patient_invitation(
        actor=actor,
        room=room,
    )
    template_slug = (
        "telemedicine-link-regenerated"
        if had_active_invitation
        else "telemedicine-invitation"
    )
    communication = _create_telemedicine_communication(
        actor=actor,
        room=room,
        channel=channel,
        template_slug=template_slug,
        source_event="telemedicine.invitation.created",
        idempotency_key=f"telemedicine-invitation:{invitation.pk}:{channel}",
        invitation_url=invitation_url,
    )
    _schedule_telemedicine_reminder(
        actor=actor,
        room=room,
        channel=channel,
        invitation=invitation,
        invitation_url=invitation_url,
    )
    return communication


def _latest_invitation_communication(
    room: TelemedicineRoom,
) -> Communication | None:
    return (
        Communication.objects.filter(
            organization=room.organization,
            appointment=room.appointment,
            source_event="telemedicine.invitation.created",
        )
        .exclude(status=Communication.Status.DRAFT)
        .order_by("-created_at")
        .first()
    )


def _cancel_pending_telemedicine_communications(room: TelemedicineRoom) -> int:
    return Communication.objects.filter(
        organization=room.organization,
        appointment=room.appointment,
        source_event__startswith="telemedicine.",
        status__in=[
            Communication.Status.SCHEDULED,
            Communication.Status.QUEUED,
            Communication.Status.FAILED,
        ],
    ).update(
        status=Communication.Status.CANCELED,
        canceled_at=timezone.now(),
        updated_at=timezone.now(),
    )


def synchronize_sent_telemedicine_communications(
    *,
    actor,
    room: TelemedicineRoom,
    previous_start_time,
    previous_status: str,
    previous_modality: str,
) -> None:
    """Mantém comunicações já iniciadas coerentes com alterações da consulta."""

    latest = _latest_invitation_communication(room)
    if latest is None:
        return

    appointment = room.appointment
    became_unavailable = (
        appointment.status == Appointment.Status.CANCELLED
        or appointment.modality == Appointment.Modality.IN_PERSON
    )
    changed_schedule = previous_start_time != appointment.start_time
    status_changed = previous_status != appointment.status
    modality_changed = previous_modality != appointment.modality

    if became_unavailable and (status_changed or modality_changed):
        _cancel_pending_telemedicine_communications(room)
        try:
            _create_telemedicine_communication(
                actor=actor,
                room=room,
                channel=latest.channel,
                template_slug="telemedicine-canceled",
                source_event="telemedicine.appointment.canceled",
                idempotency_key=(
                    f"telemedicine-canceled:{room.pk}:{latest.channel}:"
                    f"{appointment.updated_at.isoformat()}"
                ),
            )
        except Exception as exc:
            logger.warning(
                "telemedicine_cancellation_communication_failed",
                extra={
                    "organization_id": str(room.organization_id),
                    "exception_type": exc.__class__.__name__,
                },
            )
        return

    if not changed_schedule:
        return
    if appointment.status not in {
        Appointment.Status.SCHEDULED,
        Appointment.Status.CONFIRMED,
        Appointment.Status.RESCHEDULED,
    }:
        _cancel_pending_telemedicine_communications(room)
        return

    _cancel_pending_telemedicine_communications(room)
    try:
        send_telemedicine_invitation(
            actor=actor,
            room=room,
            channel=latest.channel,
        )
    except Exception as exc:
        logger.warning(
            "telemedicine_reschedule_communication_failed",
            extra={
                "organization_id": str(room.organization_id),
                "exception_type": exc.__class__.__name__,
            },
        )
