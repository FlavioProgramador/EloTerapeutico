"""Consultas de leitura para templates de documentos."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.documents.models import DocumentTemplate


def owned_templates(*, owner) -> QuerySet[DocumentTemplate]:
    return DocumentTemplate.objects.filter(
        owner=owner,
        is_library_template=False,
    ).select_related("created_by", "source_library_template")


def library_templates() -> QuerySet[DocumentTemplate]:
    return DocumentTemplate.objects.filter(
        owner__isnull=True,
        is_library_template=True,
        status=DocumentTemplate.Status.ACTIVE,
        archived_at__isnull=True,
    ).select_related("created_by")


def get_owned_template(*, owner, public_id) -> DocumentTemplate | None:
    return DocumentTemplate.objects.filter(
        public_id=public_id,
        owner=owner,
        is_library_template=False,
        archived_at__isnull=True,
    ).first()


def template_name_exists(*, owner, name: str, exclude_id: int | None = None) -> bool:
    queryset = DocumentTemplate.objects.filter(
        owner=owner,
        name=name,
        archived_at__isnull=True,
    )
    if exclude_id is not None:
        queryset = queryset.exclude(pk=exclude_id)
    return queryset.exists()


def find_imported_template(*, owner, library_template: DocumentTemplate) -> DocumentTemplate | None:
    return DocumentTemplate.objects.filter(
        owner=owner,
        source_library_template=library_template,
        archived_at__isnull=True,
    ).first()
