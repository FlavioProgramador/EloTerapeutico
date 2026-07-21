"""Consultas de leitura para templates de documentos."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.documents.models import DocumentTemplate


def owned_templates(*, owner, organization=None) -> QuerySet[DocumentTemplate]:
    queryset = DocumentTemplate.objects.filter(
        owner=owner,
        is_library_template=False,
    ).select_related("organization", "created_by", "source_library_template")
    return queryset.filter(organization=organization) if organization else queryset


def organization_templates(*, organization) -> QuerySet[DocumentTemplate]:
    return DocumentTemplate.objects.filter(
        organization=organization,
        is_library_template=False,
        archived_at__isnull=True,
    ).select_related("owner", "created_by", "source_library_template")


def library_templates() -> QuerySet[DocumentTemplate]:
    return DocumentTemplate.objects.filter(
        organization__isnull=True,
        owner__isnull=True,
        is_library_template=True,
        status=DocumentTemplate.Status.ACTIVE,
        archived_at__isnull=True,
    ).select_related("created_by")


def get_owned_template(*, owner, public_id, organization=None) -> DocumentTemplate | None:
    queryset = DocumentTemplate.objects.filter(
        public_id=public_id,
        owner=owner,
        is_library_template=False,
        archived_at__isnull=True,
    )
    if organization is not None:
        queryset = queryset.filter(organization=organization)
    return queryset.first()


def template_name_exists(
    *,
    organization,
    name: str,
    exclude_id: int | None = None,
) -> bool:
    queryset = DocumentTemplate.objects.filter(
        organization=organization,
        is_library_template=False,
        name=name,
        archived_at__isnull=True,
    )
    if exclude_id is not None:
        queryset = queryset.exclude(pk=exclude_id)
    return queryset.exists()


def find_imported_template(
    *,
    organization,
    library_template: DocumentTemplate,
) -> DocumentTemplate | None:
    return DocumentTemplate.objects.filter(
        organization=organization,
        source_library_template=library_template,
        archived_at__isnull=True,
    ).first()
