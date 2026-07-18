"""Orquestração transacional da geração e persistência de PDFs."""

from __future__ import annotations

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.documents.exceptions import DocumentDomainError
from apps.documents.infrastructure.pdf import render_document_pdf
from apps.documents.models import GeneratedDocument
from apps.documents.services.access import ensure_document_access


def generate_pdf(*, document: GeneratedDocument, actor) -> GeneratedDocument:
    """Gera o PDF mantendo exclusão mútua e transições de estado consistentes."""

    with transaction.atomic():
        locked = GeneratedDocument.objects.select_for_update().get(pk=document.pk)
        ensure_document_access(actor=actor, document=locked)
        if locked.status == GeneratedDocument.Status.COMPLETED and locked.pdf_file:
            return locked
        if locked.status in (
            GeneratedDocument.Status.CANCELLED,
            GeneratedDocument.Status.ARCHIVED,
        ):
            raise DocumentDomainError("Este documento não pode ser gerado no status atual.")
        if locked.status == GeneratedDocument.Status.PROCESSING:
            raise DocumentDomainError("Este documento já está sendo processado.")
        locked.status = GeneratedDocument.Status.PROCESSING
        locked.failure_reason = ""
        locked.save(update_fields=["status", "failure_reason", "updated_at"])

    try:
        document = GeneratedDocument.objects.get(pk=document.pk)
        pdf_bytes = render_document_pdf(document)
    except Exception as exc:
        GeneratedDocument.objects.filter(pk=document.pk).update(
            status=GeneratedDocument.Status.FAILED,
            failure_reason="Não foi possível gerar o PDF. Tente novamente.",
            updated_at=timezone.now(),
        )
        raise DocumentDomainError("Falha ao gerar o PDF do documento.") from exc

    with transaction.atomic():
        locked = GeneratedDocument.objects.select_for_update().get(pk=document.pk)
        ensure_document_access(actor=actor, document=locked)
        if locked.status != GeneratedDocument.Status.PROCESSING:
            raise DocumentDomainError("O estado do documento mudou durante a geração.")
        pdf_hash = GeneratedDocument.calculate_hash(pdf_bytes)
        generated_at = timezone.now()
        signature_hash = GeneratedDocument.calculate_hash(
            f"{pdf_hash}:{locked.professional_id}:{generated_at.isoformat()}".encode()
        )
        filename = f"{locked.document_number}.pdf"
        locked.pdf_file.save(filename, ContentFile(pdf_bytes), save=False)
        locked.pdf_hash = pdf_hash
        locked.signature_hash = signature_hash
        locked.generated_at = generated_at
        locked.signed_at = generated_at if locked.requires_signature_snapshot else None
        locked.status = GeneratedDocument.Status.COMPLETED
        locked.save(
            update_fields=[
                "pdf_file",
                "pdf_hash",
                "signature_hash",
                "generated_at",
                "signed_at",
                "status",
                "updated_at",
            ]
        )
        return locked
