from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.communications.models import Communication, CommunicationTemplate
from apps.communications.services import create_communication
from apps.scheduling.models import TelemedicineInvitation, TelemedicineRoom
from apps.scheduling.services.telemedicine_access import create_patient_invitation
from apps.scheduling.services.telemedicine_rooms import validate_professional_access

ALLOWED_INVITATION_CHANNELS = {
    Communication.Channel.EMAIL,
    Communication.Channel.WHATSAPP_MANUAL,
}


@transaction.atomic
def send_telemedicine_invitation(
    *,
    actor,
    room: TelemedicineRoom,
    channel: str = Communication.Channel.EMAIL,
) -> Communication:
    """Gera um convite novo e o enfileira pelo módulo canônico de comunicações."""

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
    template = CommunicationTemplate.objects.filter(
        organization__isnull=True,
        owner__isnull=True,
        is_system_template=True,
        is_active=True,
        is_archived=False,
        slug=template_slug,
        channel=channel,
    ).first()
    if template is None:
        raise ValidationError(
            "O modelo de convite online ainda não está disponível."
        )

    appointment = room.appointment
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
        idempotency_key=(
            f"telemedicine-invitation:{invitation.pk}:{channel}"
        ),
        source_event="telemedicine.invitation.created",
        source_object_type="TelemedicineRoom",
        source_object_id=str(room.public_id),
        metadata={"event_version": "1"},
    )
