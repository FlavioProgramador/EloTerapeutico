"""Casos de uso de documentos gerados."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from django.db import IntegrityError, models, transaction

from apps.documents.exceptions import DocumentDomainError
from apps.documents.models import DocumentTemplate, GeneratedDocument
from apps.documents.selectors import find_by_idempotency_key
from apps.documents.services.access import ensure_document_access, ensure_patient_access, ensure_template_access
from apps.documents.services.placeholders import (
    build_document_context,
    render_safe_markdown,
    validate_template_content,
)
from apps.documents.services.sequences import reserve_document_number
from apps.patients.models import Patient


@dataclass(frozen=True)
class GeneratedDocumentResult:
    document: GeneratedDocument
    created: bool


@dataclass(frozen=True)
class DocumentRemovalResult:
    """Resultado da política de remoção de um documento gerado."""

    object_id: int
    archived: bool
    document: GeneratedDocument | None


@dataclass(frozen=True)
class DocumentDownload:
    """Arquivo validado e preparado para resposta HTTP privada."""

    file: Any
    filename: str
    content_type: str = "application/pdf"


@transaction.atomic
def create_generated_document(
    *,
    actor,
    patient: Patient,
    template: DocumentTemplate,
    title: str,
    local_emissao: str = "",
    idempotency_key: str | None = None,
) -> GeneratedDocumentResult:
    ensure_patient_access(actor=actor, patient=patient)
    ensure_template_access(actor=actor, template=template)

    normalized_key = (idempotency_key or "").strip() or None
    if normalized_key and len(normalized_key) > 128:
        raise DocumentDomainError("A chave de idempotência deve possuir no máximo 128 caracteres.")
    if normalized_key:
        existing = find_by_idempotency_key(owner=actor, idempotency_key=normalized_key)
        if existing:
            return GeneratedDocumentResult(document=existing, created=False)

    number = reserve_document_number(owner=actor)
    context = build_document_context(
        patient=patient,
        professional=actor,
        document_number=number,
        local_emissao=local_emissao,
    )
    validate_template_content(template.content)
    rendered = render_safe_markdown(template.content, context)

    try:
        document = GeneratedDocument.objects.create(
            owner=actor,
            professional=actor,
            patient=patient,
            template=template,
            title=title.strip() or template.name,
            document_type=template.document_type,
            category=template.category,
            document_number=number,
            template_name_snapshot=template.name,
            template_version_snapshot=template.version,
            template_content_snapshot=template.content,
            template_header_snapshot=template.header_content,
            template_footer_snapshot=template.footer_content,
            include_professional_identification_snapshot=template.include_professional_identification,
            include_clinic_identification_snapshot=template.include_clinic_identification,
            requires_signature_snapshot=template.requires_signature,
            rendered_content=rendered,
            context_snapshot=json.dumps(context, ensure_ascii=False),
            professional_name_snapshot=actor.full_name,
            professional_registration_snapshot=actor.crp_number or "",
            idempotency_key=normalized_key,
        )
    except IntegrityError:
        if normalized_key:
            existing = find_by_idempotency_key(owner=actor, idempotency_key=normalized_key)
            if existing:
                return GeneratedDocumentResult(document=existing, created=False)
        raise

    DocumentTemplate.objects.filter(pk=template.pk).update(usage_count=models.F("usage_count") + 1)
    return GeneratedDocumentResult(document=document, created=True)


@transaction.atomic
def update_document_draft(
    *,
    document: GeneratedDocument,
    validated_data: dict,
    actor=None,
) -> GeneratedDocument:
    if actor is not None:
        ensure_document_access(actor=actor, document=document)
    if document.status != GeneratedDocument.Status.DRAFT:
        raise DocumentDomainError("Somente documentos em rascunho podem ser editados.")
    for field, value in validated_data.items():
        setattr(document, field, value)
    context = json.loads(document.context_snapshot or "{}")
    document.rendered_content = render_safe_markdown(document.template_content_snapshot, context)
    document.save()
    return document


@transaction.atomic
def archive_document(*, document: GeneratedDocument, actor=None) -> GeneratedDocument:
    if actor is not None:
        ensure_document_access(actor=actor, document=document)
    document.archive()
    return document


@transaction.atomic
def remove_or_archive_document(*, actor, document: GeneratedDocument) -> DocumentRemovalResult:
    """Exclui rascunhos sem arquivo e arquiva documentos com histórico."""

    ensure_document_access(actor=actor, document=document)
    object_id = document.pk
    if document.status == GeneratedDocument.Status.DRAFT and not document.pdf_file:
        document.delete()
        return DocumentRemovalResult(object_id=object_id, archived=False, document=None)
    archived = archive_document(actor=actor, document=document)
    return DocumentRemovalResult(object_id=object_id, archived=True, document=archived)


@transaction.atomic
def cancel_document(*, document: GeneratedDocument, actor=None) -> GeneratedDocument:
    if actor is not None:
        ensure_document_access(actor=actor, document=document)
    if document.status not in (
        GeneratedDocument.Status.DRAFT,
        GeneratedDocument.Status.FAILED,
    ):
        raise DocumentDomainError("Somente rascunhos ou documentos com falha podem ser cancelados.")
    document.status = GeneratedDocument.Status.CANCELLED
    document.save(update_fields=["status", "updated_at"])
    return document


def prepare_document_download(*, actor, document: GeneratedDocument) -> DocumentDownload:
    """Valida acesso e disponibilidade antes de abrir o arquivo privado."""

    ensure_document_access(actor=actor, document=document)
    if document.status != GeneratedDocument.Status.COMPLETED or not document.pdf_file:
        raise DocumentDomainError("O arquivo ainda não está disponível.")
    document.pdf_file.open("rb")
    return DocumentDownload(
        file=document.pdf_file,
        filename=f"{document.document_number}.pdf",
    )
