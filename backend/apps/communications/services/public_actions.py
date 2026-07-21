from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from ..models import PublicCommunicationActionToken
from .automations import cancel_pending_for_source


def issue_appointment_action_links(owner, patient, appointment) -> dict[str, str]:
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    result = {}
    purposes = {
        "confirmation_link": PublicCommunicationActionToken.Purpose.CONFIRM_APPOINTMENT,
        "cancellation_link": PublicCommunicationActionToken.Purpose.CANCEL_REQUEST,
        "reschedule_link": PublicCommunicationActionToken.Purpose.RESCHEDULE_REQUEST,
    }
    for variable, purpose in purposes.items():
        _, raw = PublicCommunicationActionToken.issue(
            owner=owner,
            patient=patient,
            appointment=appointment,
            purpose=purpose,
            ttl_hours=72,
        )
        result[variable] = f"{frontend_url}/comunicacoes/acao/{raw}"
    return result


def issue_form_access_link(owner, patient, submission) -> str:
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    _, raw = PublicCommunicationActionToken.issue(
        owner=owner,
        patient=patient,
        form_submission=submission,
        purpose=PublicCommunicationActionToken.Purpose.FORM_ACCESS,
        ttl_hours=168,
    )
    return f"{frontend_url}/comunicacoes/acao/{raw}"


def issue_document_access_link(owner, patient, document) -> str:
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    _, raw = PublicCommunicationActionToken.issue(
        owner=owner,
        patient=patient,
        document=document,
        purpose=PublicCommunicationActionToken.Purpose.DOCUMENT_ACCESS,
        ttl_hours=72,
    )
    return f"{frontend_url}/comunicacoes/acao/{raw}"


def public_action_context(raw_token: str) -> dict[str, object] | None:
    token = PublicCommunicationActionToken.resolve(raw_token)
    if token is None:
        return None
    payload: dict[str, object] = {
        "status": "valid",
        "purpose": token.purpose,
        "clinic_name": token.owner.clinic_name or "Elo Terapêutico",
        "expires_at": token.expires_at,
    }
    if (
        token.purpose == PublicCommunicationActionToken.Purpose.FORM_ACCESS
        and token.form_submission_id
    ):
        submission = token.form_submission
        if submission.status != submission.Status.DRAFT:
            return None
        payload["form"] = {
            "name": submission.form.name,
            "description": submission.form.description,
            "fields": [
                {
                    "id": field.pk,
                    "type": field.type,
                    "label": field.label,
                    "placeholder": field.placeholder,
                    "help_text": field.help_text,
                    "required": field.required,
                    "config": field.config,
                }
                for field in submission.form.fields.filter(
                    is_visible=True
                ).order_by("order", "id")
            ],
        }
    elif (
        token.purpose == PublicCommunicationActionToken.Purpose.DOCUMENT_ACCESS
        and token.document_id
    ):
        document = token.document
        if document.status != document.Status.COMPLETED or not document.pdf_file:
            return None
        payload["document"] = {"name": document.title}
    return payload


def submit_public_form(
    raw_token: str,
    answers: dict[str, object],
) -> dict[str, object]:
    from apps.forms.models import FormAnswer

    token = PublicCommunicationActionToken.resolve(raw_token)
    if (
        token is None
        or token.purpose != PublicCommunicationActionToken.Purpose.FORM_ACCESS
    ):
        raise ValidationError("Não foi possível validar esta ação.")
    submission = token.form_submission
    if submission is None or submission.status != submission.Status.DRAFT:
        raise ValidationError("Não foi possível validar esta ação.")
    fields = list(
        submission.form.fields.filter(is_visible=True).order_by("order", "id")
    )
    allowed_ids = {str(field.pk): field for field in fields}
    if set(answers) - set(allowed_ids):
        raise ValidationError("O formulário contém campos inválidos.")
    for field in fields:
        raw_value = answers.get(str(field.pk))
        empty = raw_value in (None, "", [], {})
        if field.required and empty:
            raise ValidationError(f"O campo '{field.label}' é obrigatório.")
        if empty:
            continue
        if len(str(raw_value)) > 10000:
            raise ValidationError("Uma resposta excede o tamanho permitido.")
        FormAnswer.objects.update_or_create(
            submission=submission,
            field=field,
            defaults={"value": raw_value},
        )
    now = timezone.now()
    submission.status = submission.Status.SUBMITTED
    submission.submitted_at = now
    submission.submitted_by = None
    submission.save(
        update_fields=["status", "submitted_at", "submitted_by", "updated_at"]
    )
    token.used_at = now
    token.save(update_fields=["used_at"])
    from .notifications import create_notification

    create_notification(
        organization=submission.organization,
        owner=token.owner,
        recipient=token.owner,
        title="Formulário respondido",
        message=(
            "Um formulário foi respondido. "
            "Abra o módulo de Formulários para revisar."
        ),
        event_type="forms.submitted",
        category="forms",
        priority="normal",
        internal_url=f"/dashboard/formularios?submission={submission.pk}",
        action_label="Revisar formulário",
        deduplication_key=f"form-submitted:{submission.pk}",
    )
    cancel_pending_for_source(
        owner=token.owner,
        organization=submission.organization,
        source_event_prefix="form.",
        source_object_type="forms.FormSubmission",
        source_object_id=str(submission.pk),
    )
    return {
        "status": "success",
        "action": "form-submit",
        "clinic_name": token.owner.clinic_name or "Elo Terapêutico",
    }


def handle_public_action(raw_token: str, action: str):
    token = PublicCommunicationActionToken.resolve(raw_token)
    if token is None:
        raise ValidationError("Não foi possível validar esta ação.")
    appointment = token.appointment
    if appointment is None:
        raise ValidationError("Não foi possível validar esta ação.")
    expected = {
        "confirm": PublicCommunicationActionToken.Purpose.CONFIRM_APPOINTMENT,
        "cancel-request": PublicCommunicationActionToken.Purpose.CANCEL_REQUEST,
        "reschedule-request": PublicCommunicationActionToken.Purpose.RESCHEDULE_REQUEST,
    }.get(action)
    if expected != token.purpose:
        raise ValidationError("Não foi possível validar esta ação.")
    now = timezone.now()
    if action == "confirm":
        if appointment.status not in {
            appointment.Status.SCHEDULED,
            appointment.Status.CONFIRMED,
        }:
            raise ValidationError("Esta consulta não pode mais ser confirmada.")
        appointment.status = appointment.Status.CONFIRMED
        appointment.save(update_fields=["status", "updated_at"])
        title = "Consulta confirmada pelo paciente"
        notification_type = "appointment.confirmed_by_patient"
    elif action == "cancel-request":
        title = "Paciente solicitou cancelamento"
        notification_type = "appointment.cancel_requested"
    else:
        title = "Paciente solicitou reagendamento"
        notification_type = "appointment.reschedule_requested"
    from .notifications import create_notification

    create_notification(
        organization=appointment.organization,
        owner=token.owner,
        recipient=token.owner,
        title=title,
        message=(
            "Uma ação foi registrada para uma consulta. "
            "Abra a agenda para revisar."
        ),
        event_type=notification_type,
        category="agenda",
        priority="high",
        internal_url=f"/dashboard/agenda?appointment={appointment.pk}",
        action_label="Abrir agenda",
        deduplication_key=f"{notification_type}:{appointment.pk}",
    )
    token.used_at = now
    token.save(update_fields=["used_at"])
    return {
        "status": "success",
        "action": action,
        "clinic_name": token.owner.clinic_name or "Elo Terapêutico",
    }
