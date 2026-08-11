"""Consultas de leitura para documentos gerados."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.documents.models import GeneratedDocument
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
    idempotency_key: str,
    organization=None,
    owner=None,
) -> GeneratedDocument | None:
    organization = organization or (_owner_organization(owner) if owner is not None else None)
    if organization is None:
        return None
    return GeneratedDocument.objects.filter(
        organization=organization,
        idempotency_key=idempotency_key,
    ).first()
