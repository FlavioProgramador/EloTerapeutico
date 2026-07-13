from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from apps.agenda.models import Appointment
from apps.documents.models import GeneratedDocument
from apps.financeiro.models import FinancialTransaction
from apps.forms.models import FormSubmission

from .models import PublicCommunicationActionToken
from .selectors import active_automations_for_event
from .services import cancel_pending_for_source, emit_domain_event, ensure_default_automations, ensure_default_channels, issue_appointment_action_links, issue_document_access_link, issue_form_access_link


def _capture_previous(sender, instance, fields: tuple[str, ...], attribute: str) -> None:
    if not instance.pk:
        setattr(instance, attribute, None)
        return
    setattr(instance, attribute, sender.objects.filter(pk=instance.pk).values(*fields).first())


def _has_active_automation(owner, event_type: str) -> bool:
    return active_automations_for_event(owner, event_type).exists()


@receiver(pre_save, sender=Appointment)
def capture_appointment_previous_state(sender, instance, **kwargs):
    _capture_previous(sender, instance, ("start_time", "end_time", "status", "updated_at"), "_communications_previous_state")


@receiver(post_save, sender=Appointment)
def enqueue_appointment_communications(sender, instance, created, **kwargs):
    previous = getattr(instance, "_communications_previous_state", None)

    def dispatch_event():
        source_id = str(instance.pk)
        version = instance.updated_at.isoformat() if instance.updated_at else "1"
        created_event = created and _has_active_automation(instance.therapist, "appointment.created")
        reminder_event = _has_active_automation(instance.therapist, "appointment.reminder_due")
        rescheduled = bool(previous and previous["start_time"] != instance.start_time)
        rescheduled_event = rescheduled and _has_active_automation(instance.therapist, "appointment.rescheduled")
        canceled = bool(previous and previous["status"] != instance.status and instance.status == Appointment.Status.CANCELLED)
        canceled_event = canceled and _has_active_automation(instance.therapist, "appointment.canceled")
        links_required = created_event or reminder_event or rescheduled_event
        links = issue_appointment_action_links(instance.therapist, instance.patient, instance) if links_required else {}
        if created:
            if created_event:
                emit_domain_event(owner=instance.therapist, event_type="appointment.created", patient=instance.patient, appointment=instance, source_object_type="agenda.Appointment", source_object_id=source_id, variables=links, event_version=version)
            if reminder_event:
                emit_domain_event(owner=instance.therapist, event_type="appointment.reminder_due", patient=instance.patient, appointment=instance, source_object_type="agenda.Appointment", source_object_id=source_id, variables=links, event_version=version)
            return
        if rescheduled:
            cancel_pending_for_source(owner=instance.therapist, source_event_prefix="appointment.", source_object_type="agenda.Appointment", source_object_id=source_id)
            PublicCommunicationActionToken.objects.filter(owner=instance.therapist, appointment=instance, used_at__isnull=True, revoked_at__isnull=True).update(revoked_at=timezone.now())
            links = issue_appointment_action_links(instance.therapist, instance.patient, instance) if rescheduled_event or reminder_event else {}
            if rescheduled_event:
                emit_domain_event(owner=instance.therapist, event_type="appointment.rescheduled", patient=instance.patient, appointment=instance, source_object_type="agenda.Appointment", source_object_id=source_id, variables=links, event_version=version)
            if reminder_event:
                emit_domain_event(owner=instance.therapist, event_type="appointment.reminder_due", patient=instance.patient, appointment=instance, source_object_type="agenda.Appointment", source_object_id=source_id, variables=links, event_version=version)
        if previous and previous["status"] != instance.status:
            if instance.status == Appointment.Status.CANCELLED:
                cancel_pending_for_source(owner=instance.therapist, source_event_prefix="appointment.", source_object_type="agenda.Appointment", source_object_id=source_id)
                PublicCommunicationActionToken.objects.filter(owner=instance.therapist, appointment=instance, used_at__isnull=True, revoked_at__isnull=True).update(revoked_at=timezone.now())
                if canceled_event:
                    emit_domain_event(owner=instance.therapist, event_type="appointment.canceled", patient=instance.patient, appointment=instance, source_object_type="agenda.Appointment", source_object_id=source_id, variables={}, event_version=version)
            elif instance.status == Appointment.Status.CONFIRMED:
                emit_domain_event(owner=instance.therapist, event_type="appointment.confirmed", patient=instance.patient, appointment=instance, source_object_type="agenda.Appointment", source_object_id=source_id, variables=links, event_version=version)

    transaction.on_commit(dispatch_event)


@receiver(pre_save, sender=FormSubmission)
def capture_form_submission_previous_state(sender, instance, **kwargs):
    _capture_previous(sender, instance, ("status", "updated_at"), "_communications_previous_state")


@receiver(post_save, sender=FormSubmission)
def enqueue_form_submission_communications(sender, instance, created, **kwargs):
    previous = getattr(instance, "_communications_previous_state", None)
    if instance.patient_id is None:
        return

    def dispatch_event():
        source_id = str(instance.pk)
        version = instance.updated_at.isoformat() if instance.updated_at else "1"
        if created and instance.status == FormSubmission.Status.DRAFT:
            if not _has_active_automation(instance.owner, "form.assigned"):
                return
            form_link = issue_form_access_link(instance.owner, instance.patient, instance)
            emit_domain_event(owner=instance.owner, event_type="form.assigned", patient=instance.patient, form_submission=instance, source_object_type="forms.FormSubmission", source_object_id=source_id, variables={"form_name": instance.form.name, "form_link": form_link}, event_version=version)
            return
        if previous and previous["status"] != instance.status and instance.status == FormSubmission.Status.SUBMITTED:
            cancel_pending_for_source(owner=instance.owner, source_event_prefix="form.", source_object_type="forms.FormSubmission", source_object_id=source_id)
            PublicCommunicationActionToken.objects.filter(owner=instance.owner, form_submission=instance, used_at__isnull=True, revoked_at__isnull=True).update(revoked_at=timezone.now())
            emit_domain_event(owner=instance.owner, event_type="form.submitted", patient=instance.patient, form_submission=instance, source_object_type="forms.FormSubmission", source_object_id=source_id, variables={"form_name": instance.form.name}, event_version=version)

    transaction.on_commit(dispatch_event)


@receiver(pre_save, sender=GeneratedDocument)
def capture_document_previous_state(sender, instance, **kwargs):
    _capture_previous(sender, instance, ("status", "signed_at", "updated_at"), "_communications_previous_state")


@receiver(post_save, sender=GeneratedDocument)
def enqueue_document_communications(sender, instance, created, **kwargs):
    previous = getattr(instance, "_communications_previous_state", None)

    def dispatch_event():
        source_id = str(instance.pk)
        version = instance.updated_at.isoformat() if instance.updated_at else "1"
        became_available = instance.status == GeneratedDocument.Status.COMPLETED and (created or not previous or previous["status"] != GeneratedDocument.Status.COMPLETED)
        if became_available and _has_active_automation(instance.owner, "document.available"):
            document_link = issue_document_access_link(instance.owner, instance.patient, instance)
            emit_domain_event(owner=instance.owner, event_type="document.available", patient=instance.patient, document=instance, source_object_type="documents.GeneratedDocument", source_object_id=source_id, variables={"document_name": instance.title, "document_link": document_link}, event_version=version)
        if previous and previous["signed_at"] is None and instance.signed_at is not None:
            cancel_pending_for_source(owner=instance.owner, source_event_prefix="document.", source_object_type="documents.GeneratedDocument", source_object_id=source_id)
            emit_domain_event(owner=instance.owner, event_type="document.signed", patient=instance.patient, document=instance, source_object_type="documents.GeneratedDocument", source_object_id=source_id, variables={"document_name": instance.title}, event_version=version)

    transaction.on_commit(dispatch_event)


@receiver(pre_save, sender=FinancialTransaction)
def capture_financial_previous_state(sender, instance, **kwargs):
    _capture_previous(sender, instance, ("payment_status", "due_date", "updated_at"), "_communications_previous_state")


@receiver(post_save, sender=FinancialTransaction)
def enqueue_financial_communications(sender, instance, created, **kwargs):
    previous = getattr(instance, "_communications_previous_state", None)
    if instance.patient_id is None or instance.transaction_type != FinancialTransaction.TransactionType.INCOME:
        return

    def dispatch_event():
        source_id = str(instance.pk)
        version = instance.updated_at.isoformat() if instance.updated_at else "1"
        amount = Decimal(str(instance.amount))
        variables = {"payment_amount": f"R$ {amount:.2f}", "payment_due_date": instance.due_date.strftime("%d/%m/%Y") if instance.due_date else "", "payment_status": instance.get_payment_status_display()}
        if created:
            emit_domain_event(owner=instance.therapist, event_type="financial.payment_created", patient=instance.patient, financial_transaction=instance, source_object_type="financeiro.FinancialTransaction", source_object_id=source_id, variables=variables, event_version=version)
        if previous and previous["payment_status"] != instance.payment_status:
            if instance.payment_status == FinancialTransaction.PaymentStatus.PAID:
                cancel_pending_for_source(owner=instance.therapist, source_event_prefix="financial.", source_object_type="financeiro.FinancialTransaction", source_object_id=source_id)
                emit_domain_event(owner=instance.therapist, event_type="financial.payment_confirmed", patient=instance.patient, financial_transaction=instance, source_object_type="financeiro.FinancialTransaction", source_object_id=source_id, variables=variables, event_version=version)
            elif instance.payment_status in {FinancialTransaction.PaymentStatus.CANCELLED, FinancialTransaction.PaymentStatus.REFUNDED}:
                cancel_pending_for_source(owner=instance.therapist, source_event_prefix="financial.", source_object_type="financeiro.FinancialTransaction", source_object_id=source_id)

    transaction.on_commit(dispatch_event)


@receiver(post_save, sender=get_user_model())
def bootstrap_user_communications(sender, instance, created, **kwargs):
    if not created:
        return

    def bootstrap():
        ensure_default_channels(instance)
        ensure_default_automations(instance)

    transaction.on_commit(bootstrap)
