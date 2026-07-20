"""Geração idempotente de comunicações operacionais recorrentes."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from apps.communications.models import PublicCommunicationActionToken
from apps.communications.selectors import active_automations_for_event
from apps.communications.services.automations import emit_domain_event
from apps.communications.services.public_actions import issue_document_access_link, issue_form_access_link
from apps.documents.models import GeneratedDocument
from apps.finances.models import FinancialTransaction
from apps.finances.selectors import transactions_requiring_reminder
from apps.forms.models import FormSubmission
from apps.scheduling.models import PatientPackage


def schedule_operational_automations(
    *,
    due_days: int = 3,
    form_reminder_hours: int = 24,
    document_reminder_hours: int = 24,
) -> dict[str, int]:
    today = timezone.localdate()
    due_limit = today + timedelta(days=max(due_days, 0))
    now = timezone.now()
    counters = {"finance": 0, "forms": 0, "documents": 0, "packages": 0}

    transactions = transactions_requiring_reminder(today=today, due_limit=due_limit)
    for financial_transaction in transactions.iterator(chunk_size=200):
        if financial_transaction.due_date < today:
            event_type = "financial.payment_overdue"
        elif financial_transaction.due_date <= due_limit:
            event_type = "financial.payment_due_soon"
        else:
            continue
        created = emit_domain_event(
            owner=financial_transaction.therapist,
            event_type=event_type,
            patient=financial_transaction.patient,
            financial_transaction=financial_transaction,
            source_object_type=FinancialTransaction._meta.label,
            source_object_id=str(financial_transaction.pk),
            variables={
                "payment_amount": f"R$ {financial_transaction.outstanding_amount:.2f}",
                "payment_due_date": financial_transaction.due_date.strftime("%d/%m/%Y"),
                "payment_status": financial_transaction.get_payment_status_display(),
            },
            event_version=f"{financial_transaction.updated_at.isoformat()}:{today.isoformat()}",
        )
        counters["finance"] += len(created)

    form_cutoff = now - timedelta(hours=max(form_reminder_hours, 1))
    submissions = FormSubmission.objects.filter(
        status=FormSubmission.Status.DRAFT,
        patient__isnull=False,
        created_at__lte=form_cutoff,
    ).select_related("owner", "patient", "form")
    for submission in submissions.iterator(chunk_size=200):
        if not active_automations_for_event(submission.owner, "form.due_soon").exists():
            continue
        PublicCommunicationActionToken.objects.filter(
            owner=submission.owner,
            form_submission=submission,
            purpose=PublicCommunicationActionToken.Purpose.FORM_ACCESS,
            used_at__isnull=True,
            revoked_at__isnull=True,
            expires_at__gt=now,
        ).update(revoked_at=now)
        form_link = issue_form_access_link(submission.owner, submission.patient, submission)
        created = emit_domain_event(
            owner=submission.owner,
            event_type="form.due_soon",
            patient=submission.patient,
            form_submission=submission,
            source_object_type="forms.FormSubmission",
            source_object_id=str(submission.pk),
            variables={"form_name": submission.form.name, "form_link": form_link},
            event_version=today.isoformat(),
        )
        counters["forms"] += len(created)

    packages = PatientPackage.objects.filter(
        status=PatientPackage.Status.ACTIVE,
        sessions_contracted__gt=0,
    ).select_related("therapist", "patient")
    for package in packages.iterator(chunk_size=200):
        remaining = package.remaining_sessions
        if remaining <= 0 or remaining > 2:
            continue
        created = emit_domain_event(
            owner=package.therapist,
            event_type="financial.package_ending",
            patient=package.patient,
            source_object_type="agenda.PatientPackage",
            source_object_id=str(package.pk),
            variables={"package_remaining_sessions": remaining},
            event_version=f"{package.updated_at.isoformat()}:{remaining}",
        )
        counters["packages"] += len(created)

    document_cutoff = now - timedelta(hours=max(document_reminder_hours, 1))
    documents = GeneratedDocument.objects.filter(
        status=GeneratedDocument.Status.COMPLETED,
        requires_signature_snapshot=True,
        signed_at__isnull=True,
        created_at__lte=document_cutoff,
    ).select_related("owner", "patient")
    for document in documents.iterator(chunk_size=200):
        if not active_automations_for_event(document.owner, "document.signature_requested").exists():
            continue
        PublicCommunicationActionToken.objects.filter(
            owner=document.owner,
            document=document,
            purpose=PublicCommunicationActionToken.Purpose.DOCUMENT_ACCESS,
            used_at__isnull=True,
            revoked_at__isnull=True,
        ).update(revoked_at=now)
        document_link = issue_document_access_link(document.owner, document.patient, document)
        created = emit_domain_event(
            owner=document.owner,
            event_type="document.signature_requested",
            patient=document.patient,
            document=document,
            source_object_type="documents.GeneratedDocument",
            source_object_id=str(document.pk),
            variables={"document_name": document.title, "document_link": document_link},
            event_version=today.isoformat(),
        )
        counters["documents"] += len(created)

    return counters
