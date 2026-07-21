"""Consultas de leitura para templates de documentos."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.documents.models import DocumentTemplate
from apps.organizations.models import OrganizationMembership


def _owner_organization(owner):
    memberships = OrganizationMembership.objects.filter(
        user=owner,
        status=OrganizationMembership.Status.ACTIVE,
    ).select_related("organization")
    membership = memberships.filter(is_default=True).first()
    if membership is None:
        first_two = list(memberships[:2])
        membership = first_two[0] if len(first_two) == 1 else None
    return membership.organization if membership is not None else None


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
    name: str,
    organization=None,
    owner=None,
    exclude_id: int | None = None,
) -> bool:
    organization = organization or (_owner_organization(owner) if owner is not None else None)
    if organization is None:
        return False
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
    library_template: DocumentTemplate,
    organization=None,
    owner=None,
) -> DocumentTemplate | None:
    organization = organization or (_owner_organization(owner) if owner is not None else None)
    if organization is None:
        return None
    return DocumentTemplate.objects.filter(
        organization=organization,
        source_library_template=library_template,
        archived_at__isnull=True,
    ).first()
