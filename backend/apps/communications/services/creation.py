from __future__ import annotations

import logging
from collections.abc import Mapping

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from ..models import Communication, CommunicationChannelConfig, CommunicationRecipient
from ..validators import plain_text_to_safe_html
from .billing import enforce_communication_limit, get_plan_communication_entitlement
from .preferences import _resolve_recipient
from .privacy import CommunicationBlocked, _safe_variables
from .templates import build_default_variables, render_communication

logger = logging.getLogger(__name__)


@transaction.atomic
def create_communication(
    *,
    owner,
    created_by,
    channel: str,
    category: str,
    patient=None,
    appointment=None,
    form_submission=None,
    document=None,
    financial_transaction=None,
    template=None,
    subject: str = "",
    body: str = "",
    variables: Mapping[str, object] | None = None,
    scheduled_at=None,
    priority: str = Communication.Priority.NORMAL,
    recipient_type: str | None = None,
    idempotency_key: str,
    source_event: str = "",
    source_object_type: str = "",
    source_object_id: str = "",
    metadata: Mapping[str, object] | None = None,
    draft: bool = False,
    controlled_destination: str | None = None,
):
    if not idempotency_key:
        raise ValidationError("Idempotency key é obrigatória.")

    normalized_idempotency_key = idempotency_key[:160]
    existing = Communication.objects.filter(
        owner=owner,
        idempotency_key=normalized_idempotency_key,
    ).first()
    if existing is not None:
        return existing

    if patient is not None and patient.therapist_id != owner.pk:
        raise ValidationError("Paciente inválido para este usuário.")
    if appointment is not None and appointment.therapist_id != owner.pk:
        raise ValidationError("Consulta inválida para este usuário.")
    if form_submission is not None and form_submission.owner_id != owner.pk:
        raise ValidationError("Formulário inválido para este usuário.")
    if document is not None and document.owner_id != owner.pk:
        raise ValidationError("Documento inválido para este usuário.")
    if financial_transaction is not None and financial_transaction.therapist_id != owner.pk:
        raise ValidationError("Transação financeira inválida para este usuário.")
    if not draft:
        owner.__class__.objects.select_for_update().filter(pk=owner.pk).exists()
        enforce_communication_limit(owner, channel=channel)
        plan_entitlement = get_plan_communication_entitlement(owner)
        if plan_entitlement is not None:
            if channel == Communication.Channel.EMAIL and not plan_entitlement.email_enabled:
                raise PermissionDenied("Seu plano atual não inclui comunicações por e-mail.")
            if channel == Communication.Channel.WHATSAPP and not plan_entitlement.whatsapp_enabled:
                raise PermissionDenied("Seu plano atual não inclui WhatsApp Business.")
            if channel == Communication.Channel.SMS and not plan_entitlement.sms_enabled:
                raise PermissionDenied("Seu plano atual não inclui SMS.")
        ensure_default_channels(owner)
        config = CommunicationChannelConfig.objects.filter(owner=owner, channel=channel).first()
        if config is None or not config.is_active or config.connection_status != CommunicationChannelConfig.ConnectionStatus.CONFIGURED:
            raise CommunicationBlocked("Este canal ainda não está configurado e ativo.")

    variables_payload: dict[str, object] = build_default_variables(owner, patient, appointment)
    variables_payload.update(variables or {})
    if template is not None:
        if template.owner_id not in {None, owner.pk}:
            raise ValidationError("Template inválido para este usuário.")
        subject, body, body_html, safe_variables = render_communication(template, variables_payload)
        template_snapshot = {"id": template.pk, "name": template.name, "channel": template.channel, "subject_template": template.subject_template, "body_template": template.body_template}
    else:
        if not body.strip():
            raise ValidationError("O conteúdo da comunicação é obrigatório.")
        body_html = plain_text_to_safe_html(body)
        safe_variables = _safe_variables(variables_payload)
        template_snapshot = {}
    if scheduled_at and scheduled_at <= timezone.now():
        raise ValidationError("A data de agendamento deve estar no futuro.")

    status = Communication.Status.DRAFT if draft else (Communication.Status.SCHEDULED if scheduled_at else Communication.Status.QUEUED)
    try:
        with transaction.atomic():
            communication = Communication.objects.create(
                owner=owner,
                created_by=created_by,
                patient=patient,
                appointment=appointment,
                form_submission=form_submission,
                document=document,
                financial_transaction=financial_transaction,
                channel=channel,
                category=category,
                status=status,
                priority=priority,
                subject=subject[:255],
                body=body,
                body_html=body_html,
                template=template,
                template_snapshot=template_snapshot,
                variables_snapshot=safe_variables,
                scheduled_at=scheduled_at,
                queued_at=timezone.now() if status == Communication.Status.QUEUED else None,
                idempotency_key=normalized_idempotency_key,
                source_event=source_event[:80],
                source_object_type=source_object_type[:80],
                source_object_id=source_object_id[:80],
                metadata={key: value for key, value in (metadata or {}).items() if key in {"internal_url", "manual_opened_at", "manual_confirmed_at", "event_version"}},
            )
    except IntegrityError:
        return Communication.objects.get(
            owner=owner,
            idempotency_key=normalized_idempotency_key,
        )

    recipient_data = _resolve_recipient(owner, patient, channel, recipient_type, controlled_destination=controlled_destination, category=category)
    CommunicationRecipient.objects.create(
        communication=communication,
        patient=recipient_data["patient"],
        recipient_type=recipient_data["recipient_type"],
        name=recipient_data["name"],
        destination=recipient_data["destination"],
        destination_masked=recipient_data["destination_masked"],
        channel=channel,
        status=CommunicationRecipient.Status.READY,
    )
    logger.info("communication_created", extra={"communication_id": communication.pk, "channel": channel, "status": status})
    return communication


def cancel_communication(communication, *, actor=None):
    if communication.status not in {Communication.Status.DRAFT, Communication.Status.SCHEDULED, Communication.Status.QUEUED, Communication.Status.FAILED}:
        raise ValidationError("Esta comunicação não pode ser cancelada.")
    communication.status = Communication.Status.CANCELED
    communication.canceled_at = timezone.now()
    communication.save(update_fields=["status", "canceled_at", "updated_at"])
    return communication


def retry_communication(communication):
    if communication.status != Communication.Status.FAILED:
        raise ValidationError("Somente comunicações com falha podem ser reenfileiradas.")
    communication.status = Communication.Status.QUEUED
    communication.queued_at = timezone.now()
    communication.failed_at = None
    communication.processing_started_at = None
    communication.next_retry_at = timezone.now()
    communication.save(update_fields=["status", "queued_at", "failed_at", "processing_started_at", "next_retry_at", "updated_at"])
    return communication


def mark_manual_opened(communication):
    if communication.channel != Communication.Channel.WHATSAPP_MANUAL:
        raise ValidationError("Ação disponível somente para WhatsApp manual.")
    if not communication.metadata.get("manual_url"):
        raise ValidationError("O link manual ainda não foi preparado pelo worker.")
    communication.metadata = {**communication.metadata, "manual_opened_at": timezone.now().isoformat()}
    communication.save(update_fields=["metadata", "updated_at"])
    return communication


def mark_manually_sent(communication):
    if communication.channel != Communication.Channel.WHATSAPP_MANUAL:
        raise ValidationError("Ação disponível somente para WhatsApp manual.")
    if "manual_opened_at" not in communication.metadata:
        raise ValidationError("Abra o WhatsApp antes de confirmar o envio manual.")
    now = timezone.now()
    communication.status = Communication.Status.SENT
    communication.sent_at = now
    communication.metadata = {**communication.metadata, "manual_confirmed_at": now.isoformat()}
    communication.save(update_fields=["status", "sent_at", "metadata", "updated_at"])
    communication.recipients.update(status=CommunicationRecipient.Status.SENT)
    return communication


def ensure_default_channels(owner) -> None:
    defaults = {
        Communication.Channel.IN_APP: (True, CommunicationChannelConfig.ConnectionStatus.CONFIGURED, "in_app"),
        Communication.Channel.EMAIL: (True, CommunicationChannelConfig.ConnectionStatus.CONFIGURED, "django_email"),
        Communication.Channel.WHATSAPP_MANUAL: (True, CommunicationChannelConfig.ConnectionStatus.CONFIGURED, "whatsapp_manual"),
        Communication.Channel.WHATSAPP: (False, CommunicationChannelConfig.ConnectionStatus.NOT_CONFIGURED, ""),
        Communication.Channel.SMS: (False, CommunicationChannelConfig.ConnectionStatus.NOT_CONFIGURED, ""),
    }
    for channel, (active, status, provider) in defaults.items():
        CommunicationChannelConfig.objects.get_or_create(owner=owner, channel=channel, defaults={"is_active": active, "connection_status": status, "provider": provider})
