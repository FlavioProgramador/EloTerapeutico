"""Autenticação JWT com resolução do contexto de organização ativa."""

from __future__ import annotations

from django.conf import settings

from apps.billing.authentication import SubscriptionJWTAuthentication
from apps.organizations.services.tenant_context import resolve_request_organization


class TenantSubscriptionJWTAuthentication(SubscriptionJWTAuthentication):
    ACCESS_MANAGEMENT_PREFIXES = (
        *SubscriptionJWTAuthentication.ACCESS_MANAGEMENT_PREFIXES,
        "/api/v1/organizations/",
        "/api/v1/organization-invitations/",
    )
    OPTIONAL_TENANT_PREFIXES = (
        "/api/v1/auth/",
        "/api/v1/billing/",
        "/api/v1/organizations/",
        "/api/v1/organization-invitations/",
        "/api/schema/",
        "/api/docs/",
        "/health/",
    )

    def authenticate(self, request):
        authenticated = super().authenticate(request)
        if authenticated is None:
            request.organization = None
            request.organization_membership = None
            return None

        user, token = authenticated
        tenant_optional = request.path.startswith(self.OPTIONAL_TENANT_PREFIXES)
        required = bool(
            getattr(settings, "TENANT_ENFORCEMENT_ENABLED", False)
            and not tenant_optional
        )
        resolve_request_organization(request=request, user=user, required=required)
        return user, token


__all__ = ["TenantSubscriptionJWTAuthentication"]
