"""Casos de uso de templates de documentos."""

from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from apps.documents.exceptions import DocumentDomainError
from apps.documents.models import DocumentTemplate
from apps.documents.selectors import find_imported_template, template_name_exists
from apps.documents.services.access import ensure_template_access
from apps.organizations.models import OrganizationMembership
from apps.organizations.permissions import has_capability


@dataclass(frozen=True)
class TemplateRemovalResult:
    object_id: int
    archived: bool
    template: DocumentTemplate | None


def _resolve_membership(*, actor, organization=None):
    memberships = OrganizationMembership.objects.filter(
        user=actor,
        status=OrganizationMembership.Status.ACTIVE,
    ).select_related("organization")
    if organization is not None:
        membership = memberships.filter(organization=organization).first()
    else:
        membership = memberships.filter(is_default=True).first()
        if membership is None:
            first_two = list(memberships[:2])
            membership = first_two[0] if len(first_two) == 1 else None
    if membership is None or not has_capability(membership, "documents.manage"):
        raise DocumentDomainError(
            "Você não pode gerenciar documentos nesta organização."
        )
    return membership


def _resolve_organization(*, actor, organization=None):
    return _resolve_membership(
        actor=actor,
        organization=organization,
    ).organization


def _ensure_owned_template(
    *,
    actor,
    template: DocumentTemplate,
    organization=None,
) -> None:
    membership = _resolve_membership(
        actor=actor,
        organization=organization or template.organization,
    )
    if template.is_library_template or template.organization_id != membership.organization_id:
        raise DocumentDomainError("Template não autorizado.")
    if (
        membership.role == OrganizationMembership.Role.THERAPIST
        and template.owner_id != actor.id
    ):
        raise DocumentDomainError("Template pertence a outro profissional.")


def _available_template_name(*, organization, base_name: str) -> str:
    name = base_name
    suffix = 2
    while template_name_exists(organization=organization, name=name):
        name = f"{base_name} ({suffix})"
        suffix += 1
    return name


@transaction.atomic
def create_template(*, actor, validated_data: dict, organization=None) -> DocumentTemplate:
    organization = _resolve_organization(actor=actor, organization=organization)
    return DocumentTemplate.objects.create(
        **validated_data,
        organization=organization,
        owner=actor,
        created_by=actor,
        updated_by=actor,
        is_library_template=False,
    )


@transaction.atomic
def update_template(
    *,
    actor,
    template: DocumentTemplate,
    validated_data: dict,
    organization=None,
) -> DocumentTemplate:
    _ensure_owned_template(actor=actor, template=template, organization=organization)
    for field, value in validated_data.items():
        setattr(template, field, value)
    template.updated_by = actor
    template.version += 1
    template.full_clean()
    template.save()
    return template


@transaction.atomic
def import_library_template(
    *,
    actor,
    library_template: DocumentTemplate,
    organization=None,
) -> tuple[DocumentTemplate, bool]:
    organization = _resolve_organization(actor=actor, organization=organization)
    if (
        not library_template.is_library_template
        or library_template.owner_id is not None
        or library_template.organization_id is not None
    ):
        raise DocumentDomainError("Template de biblioteca inválido.")

    existing = find_imported_template(
        organization=organization,
        library_template=library_template,
    )
    if existing:
        return existing, False

    template = DocumentTemplate.objects.create(
        organization=organization,
        owner=actor,
        source_library_template=library_template,
        name=_available_template_name(
            organization=organization,
            base_name=library_template.name,
        ),
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
def duplicate_template(
    *,
    actor,
    template: DocumentTemplate,
    organization=None,
) -> DocumentTemplate:
    organization = _resolve_organization(actor=actor, organization=organization)
    ensure_template_access(
        actor=actor,
        template=template,
        organization=organization,
    )
    return DocumentTemplate.objects.create(
        organization=organization,
        owner=actor,
        source_library_template=template.source_library_template,
        name=_available_template_name(
            organization=organization,
            base_name=f"Cópia de {template.name}",
        ),
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
def archive_template(
    *,
    template: DocumentTemplate,
    actor=None,
    organization=None,
) -> DocumentTemplate:
    if actor is not None:
        _ensure_owned_template(
            actor=actor,
            template=template,
            organization=organization,
        )
        template.updated_by = actor
    template.archive()
    if actor is not None:
        template.save(update_fields=["updated_by", "updated_at"])
    return template


@transaction.atomic
def remove_or_archive_template(
    *,
    actor,
    template: DocumentTemplate,
    organization=None,
) -> TemplateRemovalResult:
    _ensure_owned_template(actor=actor, template=template, organization=organization)
    object_id = template.pk
    if template.generated_documents.exists() or template.source_library_template_id:
        archived = archive_template(
            actor=actor,
            template=template,
            organization=organization,
        )
        return TemplateRemovalResult(
            object_id=object_id,
            archived=True,
            template=archived,
        )
    template.delete()
    return TemplateRemovalResult(
        object_id=object_id,
        archived=False,
        template=None,
    )


@transaction.atomic
def activate_template(
    *,
    actor,
    template: DocumentTemplate,
    organization=None,
) -> DocumentTemplate:
    _ensure_owned_template(actor=actor, template=template, organization=organization)
    template.status = DocumentTemplate.Status.ACTIVE
    template.archived_at = None
    template.updated_by = actor
    template.save(update_fields=["status", "archived_at", "updated_by", "updated_at"])
    return template


@transaction.atomic
def deactivate_template(
    *,
    actor,
    template: DocumentTemplate,
    organization=None,
) -> DocumentTemplate:
    _ensure_owned_template(actor=actor, template=template, organization=organization)
    template.status = DocumentTemplate.Status.INACTIVE
    template.updated_by = actor
    template.save(update_fields=["status", "updated_by", "updated_at"])
    return template
