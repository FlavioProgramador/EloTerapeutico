"""Resolução explícita e segura do tenant ativo após autenticação."""

from __future__ import annotations

from uuid import UUID

from apps.organizations.exceptions import (
    OrganizationAccessDeniedError,
    OrganizationContextRequiredError,
    OrganizationSuspendedError,
)
from apps.organizations.models import Organization
from apps.organizations.selectors import list_active_memberships_for_user

ORGANIZATION_HEADER = "HTTP_X_ORGANIZATION_ID"


def resolve_request_organization(*, request, user, required: bool = True):
    memberships = list_active_memberships_for_user(user=user)
    header_value = request.META.get(ORGANIZATION_HEADER, "").strip()

    membership = None
    if header_value:
        try:
            organization_id = UUID(header_value)
        except (TypeError, ValueError) as exc:
            raise OrganizationAccessDeniedError() from exc
        membership = memberships.filter(organization_id=organization_id).first()
        if membership is None:
            raise OrganizationAccessDeniedError()
    else:
        default_membership = memberships.filter(is_default=True).first()
        if default_membership is not None:
            membership = default_membership
        else:
            first_two = list(memberships[:2])
            if len(first_two) == 1:
                membership = first_two[0]
            elif len(first_two) > 1 and required:
                raise OrganizationContextRequiredError()

    if membership is None:
        if required:
            raise OrganizationContextRequiredError()
        request.organization = None
        request.organization_membership = None
        return None, None

    organization = membership.organization
    if organization.status == Organization.Status.SUSPENDED:
        raise OrganizationSuspendedError()
    if organization.status == Organization.Status.ARCHIVED:
        raise OrganizationAccessDeniedError()

    request.organization = organization
    request.organization_membership = membership
    return organization, membership


def ensure_request_organization(*, request, required: bool = True):
    """Resolve o tenant quando autenticações de teste ou adapters pulam o JWT canônico."""

    organization = getattr(request, "organization", None)
    membership = getattr(request, "organization_membership", None)
    if organization is not None and membership is not None:
        return organization, membership
    user = getattr(request, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        if required:
            raise OrganizationContextRequiredError()
        return None, None
    return resolve_request_organization(request=request, user=user, required=required)


def require_organization_context(request):
    organization = getattr(request, "organization", None)
    membership = getattr(request, "organization_membership", None)
    if organization is None or membership is None:
        raise OrganizationContextRequiredError()
    return organization, membership
