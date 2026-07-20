from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from datetime import time as clock_time
from datetime import timezone as datetime_timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.utils import timezone

from ..models import Communication, CommunicationAutomation, CommunicationAutomationRun, CommunicationPreference
from ..selectors import active_automations_for_event
from .creation import create_communication
from .dispatch import _sanitize_error
from .preferences import get_or_create_preference

logger = logging.getLogger(__name__)

DEFAULT_AUTOMATION_BLUEPRINTS = [
    ("Confirmação ao criar consulta", "appointment.created", "appointment-created", 0, CommunicationAutomation.DelayUnit.MINUTES, False),
    ("Lembrete 24 horas antes", "appointment.reminder_due", "appointment-reminder-24h", 24, CommunicationAutomation.DelayUnit.HOURS, True),
    ("Lembrete 2 horas antes", "appointment.reminder_due", "appointment-reminder-2h", 2, CommunicationAutomation.DelayUnit.HOURS, True),
    ("Aviso de reagendamento", "appointment.rescheduled", "appointment-rescheduled", 0, CommunicationAutomation.DelayUnit.MINUTES, False),
    ("Aviso de cancelamento", "appointment.canceled", "appointment-canceled", 0, CommunicationAutomation.DelayUnit.MINUTES, False),
    ("Envio de formulário", "form.assigned", "form-request", 0, CommunicationAutomation.DelayUnit.MINUTES, False),
    ("Lembrete de formulário pendente", "form.due_soon", "form-reminder", 0, CommunicationAutomation.DelayUnit.MINUTES, False),
    ("Documento disponível", "document.available", "document-available", 0, CommunicationAutomation.DelayUnit.MINUTES, False),
    ("Lembrete de assinatura", "document.signature_requested", "document-signature-request", 0, CommunicationAutomation.DelayUnit.MINUTES, False),
    ("Pagamento próximo do vencimento", "financial.payment_due_soon", "payment-due", 0, CommunicationAutomation.DelayUnit.MINUTES, False),
    ("Pagamento vencido", "financial.payment_overdue", "payment-overdue", 0, CommunicationAutomation.DelayUnit.MINUTES, False),
    ("Pagamento confirmado", "financial.payment_confirmed", "payment-confirmed", 0, CommunicationAutomation.DelayUnit.MINUTES, False),
    ("Pacote próximo do fim", "financial.package_ending", "package-ending", 0, CommunicationAutomation.DelayUnit.MINUTES, False),
]


def _automation_delay(automation: CommunicationAutomation) -> timedelta:
    return {CommunicationAutomation.DelayUnit.MINUTES: timedelta(minutes=automation.delay_value), CommunicationAutomation.DelayUnit.HOURS: timedelta(hours=automation.delay_value), CommunicationAutomation.DelayUnit.DAYS: timedelta(days=automation.delay_value)}[CommunicationAutomation.DelayUnit(automation.delay_unit)]


def _ordered_compare(current: object, expected: object, *, greater: bool) -> bool:
    if isinstance(current, (int, float)) and isinstance(expected, (int, float)):
        return current > expected if greater else current < expected
    if isinstance(current, str) and isinstance(expected, str):
        return current > expected if greater else current < expected
    return False


def _condition_matches(condition: dict[str, object], context: dict[str, object]) -> bool:
    field = str(condition.get("field", ""))
    operator = str(condition.get("operator", "equals"))
    expected = condition.get("value")
    current = context.get(field)
    if operator == "equals":
        return current == expected
    if operator == "not_equals":
        return current != expected
    if operator == "contains":
        return str(expected) in str(current or "")
    if operator == "is_empty":
        return current is None or current == "" or current == [] or current == {}
    if operator == "is_not_empty":
        return not (current is None or current == "" or current == [] or current == {})
    if operator == "greater_than":
        return _ordered_compare(current, expected, greater=True)
    if operator == "less_than":
        return _ordered_compare(current, expected, greater=False)
    return False


def _delivery_timezone(preference: CommunicationPreference | None) -> ZoneInfo:
    name = preference.timezone if preference and preference.timezone else getattr(settings, "COMMUNICATIONS_DEFAULT_TIMEZONE", "America/Sao_Paulo")
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("America/Sao_Paulo")


def _respect_delivery_window(value, automation: CommunicationAutomation, preference: CommunicationPreference | None):
    candidate = value or timezone.now()
    tz = _delivery_timezone(preference)
    local = timezone.localtime(candidate, tz)
    start_time = automation.allowed_start_time or (preference.allowed_start_time if preference else None)
    end_time = automation.allowed_end_time or (preference.allowed_end_time if preference else None)
    weekdays = {int(day) for day in automation.allowed_weekdays if str(day).isdigit()}
    for _ in range(8):
        if weekdays and local.weekday() not in weekdays:
            local = datetime.combine(local.date() + timedelta(days=1), start_time or clock_time(8, 0), tzinfo=tz)
            continue
        if start_time and local.timetz().replace(tzinfo=None) < start_time:
            local = datetime.combine(local.date(), start_time, tzinfo=tz)
        if end_time and local.timetz().replace(tzinfo=None) > end_time:
            local = datetime.combine(local.date() + timedelta(days=1), start_time or clock_time(8, 0), tzinfo=tz)
            continue
        break
    return local.astimezone(UTC)


def _automation_context(patient=None, appointment=None, extra: Mapping[str, object] | None = None) -> dict[str, object]:
    context = dict(extra or {})
    if patient is not None:
        context.update({"patient_has_email": bool(patient.email), "patient_has_whatsapp": bool(patient.whatsapp or patient.phone), "patient_status": patient.status})
    if appointment is not None:
        context.update({"appointment_status": appointment.status, "appointment_modality": appointment.modality})
    return context


def emit_domain_event(*, owner, event_type: str, patient=None, appointment=None, form_submission=None, document=None, financial_transaction=None, source_object_type: str = "", source_object_id: str = "", variables: Mapping[str, object] | None = None, event_version: str = "1") -> list[Communication]:
    created: list[Communication] = []
    context = _automation_context(patient, appointment, variables)
    for automation in active_automations_for_event(owner, event_type):
        idem = f"automation:{automation.pk}:{event_type}:{source_object_id}:{event_version}"
        run, run_created = CommunicationAutomationRun.objects.get_or_create(automation=automation, idempotency_key=idem, defaults={"source_event": event_type, "source_object_type": source_object_type, "source_object_id": source_object_id})
        if not run_created:
            continue
        try:
            if any(not _condition_matches(condition, context) for condition in automation.conditions):
                run.status = CommunicationAutomationRun.Status.SKIPPED
                run.skip_reason = "conditions_not_met"
                continue
            preference = get_or_create_preference(owner, patient) if patient else None
            if automation.max_executions is not None and automation.runs.filter(status=CommunicationAutomationRun.Status.CREATED).count() >= automation.max_executions:
                run.status = CommunicationAutomationRun.Status.SKIPPED
                run.skip_reason = "maximum_executions_reached"
                continue
            if automation.respect_preferences and preference and preference.general_opt_out:
                run.status = CommunicationAutomationRun.Status.SKIPPED
                run.skip_reason = "recipient_opted_out"
                continue
            scheduled_at = None
            delay = _automation_delay(automation)
            if appointment and automation.send_before_event:
                scheduled_at = appointment.start_time - delay
                if scheduled_at <= timezone.now():
                    run.status = CommunicationAutomationRun.Status.SKIPPED
                    run.skip_reason = "schedule_in_past"
                    continue
            elif automation.delay_value:
                scheduled_at = timezone.now() + delay
            adjusted_at = _respect_delivery_window(scheduled_at, automation, preference)
            if adjusted_at > timezone.now() + timedelta(seconds=2):
                scheduled_at = adjusted_at
            communication = create_communication(owner=owner, created_by=automation.created_by or owner, channel=automation.channel, category=automation.template.category, patient=patient, appointment=appointment, form_submission=form_submission, document=document, financial_transaction=financial_transaction, template=automation.template, variables=variables, scheduled_at=scheduled_at, priority=automation.priority, idempotency_key=idem, source_event=event_type, source_object_type=source_object_type, source_object_id=source_object_id, metadata={"event_version": event_version})
            run.communication = communication
            run.status = CommunicationAutomationRun.Status.CREATED
            created.append(communication)
        except Exception as exc:
            run.status = CommunicationAutomationRun.Status.FAILED
            run.error_message = _sanitize_error(exc)
            logger.warning("communication_automation_failed", extra={"automation_id": automation.pk, "exception_type": exc.__class__.__name__})
        finally:
            run.finished_at = timezone.now()
            run.save()
    return created


def cancel_pending_for_source(*, owner, source_event_prefix: str, source_object_type: str, source_object_id: str):
    return Communication.objects.filter(owner=owner, source_event__startswith=source_event_prefix, source_object_type=source_object_type, source_object_id=source_object_id, status__in=[Communication.Status.SCHEDULED, Communication.Status.QUEUED]).update(status=Communication.Status.CANCELED, canceled_at=timezone.now())


def ensure_default_automations(owner) -> None:
    from ..models import CommunicationTemplate

    for name, event_type, template_slug, delay_value, delay_unit, send_before in DEFAULT_AUTOMATION_BLUEPRINTS:
        template = CommunicationTemplate.objects.filter(owner__isnull=True, is_system_template=True, slug=template_slug, channel=Communication.Channel.EMAIL, is_active=True).first()
        if template is None:
            continue
        CommunicationAutomation.objects.get_or_create(owner=owner, name=name, defaults={"description": "Automação sugerida pelo Elo Terapêutico. Ative somente após revisar o canal e o template.", "event_type": event_type, "channel": Communication.Channel.EMAIL, "template": template, "is_active": False, "delay_value": delay_value, "delay_unit": delay_unit, "send_before_event": send_before, "respect_preferences": True, "created_by": owner, "updated_by": owner})
