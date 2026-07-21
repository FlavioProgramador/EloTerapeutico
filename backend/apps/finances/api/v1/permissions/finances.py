"""Permissões financeiras baseadas na membership ativa."""

from rest_framework.permissions import BasePermission

from apps.organizations.permissions import has_capability
from apps.organizations.services.tenant_context import ensure_request_organization


class FinancesPermission(BasePermission):
    """Autoriza leitura e escrita somente no tenant ativo."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        _, membership = ensure_request_organization(request=request, required=True)
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return has_capability(membership, "finances.view")
        return has_capability(membership, "finances.manage")

    def has_object_permission(self, request, view, obj):
        organization, membership = ensure_request_organization(
            request=request,
            required=True,
        )
        if getattr(obj, "organization_id", None) != organization.pk:
            return False
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return has_capability(membership, "finances.view")
        return has_capability(membership, "finances.manage")


FinancialPermission = FinancesPermission
