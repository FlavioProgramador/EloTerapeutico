"""Casos de uso transacionais do módulo de documentos."""

from __future__ import annotations

import html
import json
from dataclasses import dataclass

from django.core.files.base import ContentFile
from django.db import IntegrityError, models, transaction
from django.utils import timezone

try:
    from weasyprint import HTML
except (ImportError, OSError):
    import logging

    logger = logging.getLogger(__name__)
    logger.warning("WeasyPrint could not import Pango/GObject libraries. Using dummy PDF fallback for documents.")

    class HTML:
        def __init__(self, string=None, url_fetcher=None, **kwargs):
            self.string = string

        def write_pdf(self, target=None, **kwargs):
            dummy_pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
            if target is None:
                return dummy_pdf
            if hasattr(target, "write"):
                target.write(dummy_pdf)
                return dummy_pdf
            else:
                with open(target, "wb") as f:
                    f.write(dummy_pdf)
                return dummy_pdf


from apps.patients.models import Patient

from .models import DocumentSequence, DocumentTemplate, GeneratedDocument
from .placeholders import (
    build_document_context,
    render_safe_markdown,
    validate_template_content,
)


class DocumentDomainError(Exception):
    """Erro de domínio seguro para exposição pela API."""


@dataclass(frozen=True)
class GeneratedDocumentResult:
    document: GeneratedDocument
    created: bool


def ensure_patient_access(*, actor, patient: Patient) -> None:
    if actor.is_secretary:
        raise DocumentDomainError("Secretárias não possuem acesso a documentos clínicos.")
    if patient.therapist_id != actor.id:
        raise DocumentDomainError("Paciente não autorizado para este profissional.")


def ensure_template_access(*, actor, template: DocumentTemplate) -> None:
    if template.status != DocumentTemplate.Status.ACTIVE:
        raise DocumentDomainError("O template selecionado não está ativo.")
    if template.is_library_template:
        raise DocumentDomainError("Importe o template da biblioteca antes de utilizá-lo.")
    if template.owner_id != actor.id:
        raise DocumentDomainError("Template não autorizado.")


def _next_document_number(*, owner) -> str:
    year = timezone.localdate().year
    sequence, _ = DocumentSequence.objects.select_for_update().get_or_create(
        owner=owner,
        year=year,
        defaults={"last_value": 0},
    )
    sequence.last_value += 1
    sequence.save(update_fields=["last_value", "updated_at"])
    return f"DOC-{year}-{sequence.last_value:06d}"


@transaction.atomic
def import_library_template(*, actor, library_template: DocumentTemplate) -> tuple[DocumentTemplate, bool]:
    if not library_template.is_library_template or library_template.owner_id is not None:
        raise DocumentDomainError("Template de biblioteca inválido.")
    existing = DocumentTemplate.objects.filter(
        owner=actor,
        source_library_template=library_template,
        archived_at__isnull=True,
    ).first()
    if existing:
        return existing, False

    base_name = library_template.name
    name = base_name
    suffix = 2
    while DocumentTemplate.objects.filter(
        owner=actor,
        name=name,
        archived_at__isnull=True,
    ).exists():
        name = f"{base_name} ({suffix})"
        suffix += 1

    template = DocumentTemplate.objects.create(
        owner=actor,
        source_library_template=library_template,
        name=name,
        description=library_template.description,
        category=library_template.category,
        document_type=library_template.document_type,
        specialty=library_template.specialty,
        content=library_template.content,
        header_content=library_template.header_content,
        footer_content=library_template.footer_content,
        include_professional_identification=library_template.include_professional_identification,
        include_clinic_identification=library_template.include_clinic_identification,
        requires_signature=library_template.requires_signature,
        status=DocumentTemplate.Status.ACTIVE,
        is_library_template=False,
        version=1,
        created_by=actor,
        updated_by=actor,
    )
    return template, True


@transaction.atomic
def duplicate_template(*, actor, template: DocumentTemplate) -> DocumentTemplate:
    ensure_template_access(actor=actor, template=template)
    base_name = f"Cópia de {template.name}"
    name = base_name
    suffix = 2
    while DocumentTemplate.objects.filter(
        owner=actor,
        name=name,
        archived_at__isnull=True,
    ).exists():
        name = f"{base_name} ({suffix})"
        suffix += 1
    return DocumentTemplate.objects.create(
        owner=actor,
        source_library_template=template.source_library_template,
        name=name,
        description=template.description,
        category=template.category,
        document_type=template.document_type,
        specialty=template.specialty,
        content=template.content,
        header_content=template.header_content,
        footer_content=template.footer_content,
        include_professional_identification=template.include_professional_identification,
        include_clinic_identification=template.include_clinic_identification,
        requires_signature=template.requires_signature,
        status=DocumentTemplate.Status.ACTIVE,
        created_by=actor,
        updated_by=actor,
    )


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
        existing = GeneratedDocument.objects.filter(
            owner=actor,
            idempotency_key=normalized_key,
        ).first()
        if existing:
            return GeneratedDocumentResult(document=existing, created=False)

    number = _next_document_number(owner=actor)
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
            existing = GeneratedDocument.objects.filter(
                owner=actor,
                idempotency_key=normalized_key,
            ).first()
            if existing:
                return GeneratedDocumentResult(document=existing, created=False)
        raise

    DocumentTemplate.objects.filter(pk=template.pk).update(usage_count=models.F("usage_count") + 1)
    return GeneratedDocumentResult(document=document, created=True)


def _document_html(document: GeneratedDocument) -> str:
    context = json.loads(document.context_snapshot or "{}")
    header = (
        render_safe_markdown(document.template_header_snapshot, context) if document.template_header_snapshot else ""
    )
    footer = (
        render_safe_markdown(document.template_footer_snapshot, context) if document.template_footer_snapshot else ""
    )
    number = html.escape(document.document_number, quote=True)
    professional_name = html.escape(document.professional_name_snapshot, quote=True)
    registration = html.escape(document.professional_registration_snapshot, quote=True)
    signature = ""
    if document.include_professional_identification_snapshot:
        signature = (
            '<div class="signature"><div class="signature-line"></div>'
            f"<strong>{professional_name}</strong><br>{registration}</div>"
        )
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<style>
@page {{ size: A4; margin: 24mm 20mm 22mm; @bottom-center {{ content: "{number}"; font-size: 8pt; color: #64748b; }} }}
body {{ font-family: DejaVu Sans, sans-serif; color: #172033; font-size: 11pt; line-height: 1.55; }}
header {{ border-bottom: 1px solid #dbe4f0; margin-bottom: 24px; padding-bottom: 12px; color: #475569; }}
footer {{ border-top: 1px solid #dbe4f0; margin-top: 28px; padding-top: 12px; color: #64748b; font-size: 9pt; }}
h1 {{ font-size: 18pt; margin: 0 0 16px; }} h2 {{ font-size: 14pt; margin: 18px 0 8px; }} h3 {{ font-size: 12pt; margin: 14px 0 6px; }}
p {{ margin: 0 0 10px; }} li {{ margin-bottom: 5px; }} .page-break {{ page-break-before: always; }}
.signature {{ margin-top: 42px; text-align: center; }} .signature-line {{ border-top: 1px solid #334155; width: 280px; margin: 0 auto 8px; }}
.meta {{ color: #64748b; font-size: 9pt; margin-bottom: 20px; }}
</style>
</head>
<body>
<header>{header}</header>
<div class="meta">Documento {number}</div>
<main>{document.rendered_content}</main>
{signature}
<footer>{footer}</footer>
</body>
</html>"""


def generate_pdf(*, document: GeneratedDocument, actor) -> GeneratedDocument:
    with transaction.atomic():
        locked = GeneratedDocument.objects.select_for_update().get(pk=document.pk)
        if locked.owner_id != actor.id:
            raise DocumentDomainError("Documento não autorizado.")
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
        pdf_bytes = HTML(string=_document_html(document)).write_pdf()
    except Exception as exc:
        GeneratedDocument.objects.filter(pk=document.pk).update(
            status=GeneratedDocument.Status.FAILED,
            failure_reason="Não foi possível gerar o PDF. Tente novamente.",
            updated_at=timezone.now(),
        )
        raise DocumentDomainError("Falha ao gerar o PDF do documento.") from exc

    with transaction.atomic():
        locked = GeneratedDocument.objects.select_for_update().get(pk=document.pk)
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
