"""Casos de uso de documentos gerados."""

from __future__ import annotations

import json
from dataclasses import dataclass

from django.db import IntegrityError, models, transaction

from apps.documents.exceptions import DocumentDomainError
from apps.documents.models import DocumentTemplate, GeneratedDocument
from apps.documents.selectors import find_by_idempotency_key
from apps.documents.services.access import ensure_patient_access, ensure_template_access
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
def update_document_draft(*, document: GeneratedDocument, validated_data: dict) -> GeneratedDocument:
    if document.status != GeneratedDocument.Status.DRAFT:
        raise DocumentDomainError("Somente documentos em rascunho podem ser editados.")
    for field, value in validated_data.items():
        setattr(document, field, value)
    context = json.loads(document.context_snapshot or "{}")
    document.rendered_content = render_safe_markdown(document.template_content_snapshot, context)
    document.save()
    return document


@transaction.atomic
def archive_document(*, document: GeneratedDocument) -> GeneratedDocument:
    document.archive()
    return document


@transaction.atomic
def cancel_document(*, document: GeneratedDocument) -> GeneratedDocument:
    if document.status not in (
        GeneratedDocument.Status.DRAFT,
        GeneratedDocument.Status.FAILED,
    ):
        raise DocumentDomainError("Somente rascunhos ou documentos com falha podem ser cancelados.")
    document.status = GeneratedDocument.Status.CANCELLED
    document.save(update_fields=["status", "updated_at"])
    return document
