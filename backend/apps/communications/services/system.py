"""Comunicações transacionais do sistema para destinos controlados."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.communications.models import Communication, CommunicationRecipient
from apps.communications.services.creation import ensure_default_channels
from apps.communications.services.privacy import mask_email
from apps.communications.validators import plain_text_to_safe_html


@transaction.atomic
def create_system_email(
    *,
    owner,
    created_by,
    destination: str,
    subject: str,
    body: str,
    idempotency_key: str,
    source_object_type: str = "",
    source_object_id: str = "",
):
    """Cria e enfileira e-mail operacional sem associá-lo a um paciente."""

    normalized_destination = destination.strip().lower()
    if not normalized_destination or "@" not in normalized_destination:
        raise ValueError("Destino de e-mail inválido.")
    normalized_key = idempotency_key[:160]
    existing = Communication.objects.filter(
        owner=owner,
        idempotency_key=normalized_key,
    ).first()
    if existing is not None:
        return existing

    ensure_default_channels(owner)
    communication = Communication.objects.create(
        owner=owner,
        created_by=created_by,
        channel=Communication.Channel.EMAIL,
        category=Communication.Category.SYSTEM_NOTIFICATION,
        status=Communication.Status.QUEUED,
        subject=subject[:255],
        body=body,
        body_html=plain_text_to_safe_html(body),
        queued_at=timezone.now(),
        idempotency_key=normalized_key,
        source_event="system_notification",
        source_object_type=source_object_type[:80],
        source_object_id=source_object_id[:80],
        metadata={"controlled_system_destination": True},
    )
    CommunicationRecipient.objects.create(
        communication=communication,
        recipient_type=CommunicationRecipient.RecipientType.USER,
        name="Membro convidado",
        destination=normalized_destination,
        destination_masked=mask_email(normalized_destination),
        channel=Communication.Channel.EMAIL,
        status=CommunicationRecipient.Status.READY,
    )
    return communication


__all__ = ["create_system_email"]
