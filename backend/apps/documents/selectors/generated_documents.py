"""Consultas de leitura para documentos gerados."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.documents.models import GeneratedDocument
from apps.organizations.models import OrganizationMembership


def generated_documents_for_owner(
    *,
    owner,
    organization=None,
) -> QuerySet[GeneratedDocument]:
    queryset = GeneratedDocument.objects.filter(owner=owner).select_related(
        "organization",
        "patient",
        "professional",
        "template",
    )
    return queryset.filter(organization=organization) if organization else queryset


def generated_documents_for_user(*, user, organization) -> QuerySet[GeneratedDocument]:
    membership = OrganizationMembership.objects.filter(
        organization=organization,
        user=user,
        status=OrganizationMembership.Status.ACTIVE,
    ).first()
    queryset = GeneratedDocument.objects.filter(
        organization=organization
    ).select_related("patient", "professional", "template", "owner")
    if membership is None:
        return queryset.none()
    if membership.role == OrganizationMembership.Role.THERAPIST:
        return queryset.filter(professional=user)
    if membership.role in {
        OrganizationMembership.Role.OWNER,
        OrganizationMembership.Role.ADMIN,
        OrganizationMembership.Role.VIEWER,
    }:
        return queryset
    return queryset.none()


def find_by_idempotency_key(
    *,
    organization,
    idempotency_key: str,
) -> GeneratedDocument | None:
    return GeneratedDocument.objects.filter(
        organization=organization,
        idempotency_key=idempotency_key,
    ).first()
