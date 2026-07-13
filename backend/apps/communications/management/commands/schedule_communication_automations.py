from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.agenda.models import PatientPackage
from apps.communications.models import PublicCommunicationActionToken
from apps.communications.selectors import active_automations_for_event
from apps.communications.services import emit_domain_event, issue_document_access_link, issue_form_access_link
from apps.documents.models import GeneratedDocument
from apps.financeiro.models import FinancialTransaction
from apps.forms.models import FormSubmission


class Command(BaseCommand):
    help = "Agenda automações operacionais de formulários, documentos, cobranças e pacotes de forma idempotente."

    def add_arguments(self, parser):
        parser.add_argument("--due-days", type=int, default=3)
        parser.add_argument("--form-reminder-hours", type=int, default=24)
        parser.add_argument("--document-reminder-hours", type=int, default=24)

    def handle(self, *args, **options):
        today = timezone.localdate()
        due_limit = today + timedelta(days=max(options["due_days"], 0))
        now = timezone.now()
        counters = {"finance": 0, "forms": 0, "documents": 0, "packages": 0}

        transactions = FinancialTransaction.objects.filter(
            transaction_type=FinancialTransaction.TransactionType.INCOME,
            payment_status__in=[FinancialTransaction.PaymentStatus.PENDING, FinancialTransaction.PaymentStatus.PARTIAL],
            patient__isnull=False,
            due_date__isnull=False,
        ).select_related("therapist", "patient")
        for transaction in transactions.iterator():
            if transaction.due_date < today:
                event_type = "financial.payment_overdue"
            elif transaction.due_date <= due_limit:
                event_type = "financial.payment_due_soon"
            else:
                continue
            created = emit_domain_event(
                owner=transaction.therapist,
                event_type=event_type,
                patient=transaction.patient,
                financial_transaction=transaction,
                source_object_type="financeiro.FinancialTransaction",
                source_object_id=str(transaction.pk),
                variables={
                    "payment_amount": f"R$ {transaction.outstanding_amount:.2f}",
                    "payment_due_date": transaction.due_date.strftime("%d/%m/%Y"),
                    "payment_status": transaction.get_payment_status_display(),
                },
                event_version=f"{transaction.updated_at.isoformat()}:{today.isoformat()}",
            )
            counters["finance"] += len(created)

        form_cutoff = now - timedelta(hours=max(options["form_reminder_hours"], 1))
        submissions = FormSubmission.objects.filter(status=FormSubmission.Status.DRAFT, patient__isnull=False, created_at__lte=form_cutoff).select_related("owner", "patient", "form")
        for submission in submissions.iterator():
            if not active_automations_for_event(submission.owner, "form.due_soon").exists():
                continue
            PublicCommunicationActionToken.objects.filter(owner=submission.owner, form_submission=submission, purpose=PublicCommunicationActionToken.Purpose.FORM_ACCESS, used_at__isnull=True, revoked_at__isnull=True, expires_at__gt=now).update(revoked_at=now)
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

        packages = PatientPackage.objects.filter(status=PatientPackage.Status.ACTIVE, sessions_contracted__gt=0).select_related("therapist", "patient")
        for package in packages.iterator():
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

        document_cutoff = now - timedelta(hours=max(options["document_reminder_hours"], 1))
        documents = GeneratedDocument.objects.filter(status=GeneratedDocument.Status.COMPLETED, requires_signature_snapshot=True, signed_at__isnull=True, created_at__lte=document_cutoff).select_related("owner", "patient")
        for document in documents.iterator():
            if not active_automations_for_event(document.owner, "document.signature_requested").exists():
                continue
            PublicCommunicationActionToken.objects.filter(owner=document.owner, document=document, purpose=PublicCommunicationActionToken.Purpose.DOCUMENT_ACCESS, used_at__isnull=True, revoked_at__isnull=True).update(revoked_at=now)
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

        self.stdout.write(self.style.SUCCESS(f"Automações agendadas: financeiro={counters['finance']}, formulários={counters['forms']}, documentos={counters['documents']}, pacotes={counters['packages']}"))
