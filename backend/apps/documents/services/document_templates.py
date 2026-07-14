"""Casos de uso de templates de documentos."""

from __future__ import annotations

from django.db import transaction

from apps.documents.exceptions import DocumentDomainError
from apps.documents.models import DocumentTemplate
from apps.documents.selectors import find_imported_template, template_name_exists
from apps.documents.services.access import ensure_template_access


def _available_template_name(*, owner, base_name: str) -> str:
    name = base_name
    suffix = 2
    while template_name_exists(owner=owner, name=name):
        name = f"{base_name} ({suffix})"
        suffix += 1
    return name


@transaction.atomic
def create_template(*, actor, validated_data: dict) -> DocumentTemplate:
    return DocumentTemplate.objects.create(
        **validated_data,
        owner=actor,
        created_by=actor,
        updated_by=actor,
        is_library_template=False,
    )


@transaction.atomic
def update_template(*, actor, template: DocumentTemplate, validated_data: dict) -> DocumentTemplate:
    for field, value in validated_data.items():
        setattr(template, field, value)
    template.updated_by = actor
    template.version += 1
    template.save()
    return template


@transaction.atomic
def import_library_template(*, actor, library_template: DocumentTemplate) -> tuple[DocumentTemplate, bool]:
    if not library_template.is_library_template or library_template.owner_id is not None:
        raise DocumentDomainError("Template de biblioteca inválido.")

    existing = find_imported_template(owner=actor, library_template=library_template)
    if existing:
        return existing, False

    template = DocumentTemplate.objects.create(
        owner=actor,
        source_library_template=library_template,
        name=_available_template_name(owner=actor, base_name=library_template.name),
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
    return DocumentTemplate.objects.create(
        owner=actor,
        source_library_template=template.source_library_template,
        name=_available_template_name(owner=actor, base_name=f"Cópia de {template.name}"),
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
def archive_template(*, template: DocumentTemplate) -> DocumentTemplate:
    template.archive()
    return template


@transaction.atomic
def activate_template(*, actor, template: DocumentTemplate) -> DocumentTemplate:
    template.status = DocumentTemplate.Status.ACTIVE
    template.archived_at = None
    template.updated_by = actor
    template.save(update_fields=["status", "archived_at", "updated_by", "updated_at"])
    return template


@transaction.atomic
def deactivate_template(*, actor, template: DocumentTemplate) -> DocumentTemplate:
    template.status = DocumentTemplate.Status.INACTIVE
    template.updated_by = actor
    template.save(update_fields=["status", "updated_by", "updated_at"])
    return template
