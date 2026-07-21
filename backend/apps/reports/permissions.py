"""Permissões tenant-aware para relatórios e exportações."""

from rest_framework.permissions import BasePermission

from apps.organizations.permissions import has_capability
from apps.organizations.services.tenant_context import ensure_request_organization


def _request_membership(request):
    if not request.user or not request.user.is_authenticated:
        return None
    _organization, membership = ensure_request_organization(
        request=request,
        required=True,
    )
    return membership


class CanViewReports(BasePermission):
    message = "Você não possui permissão para visualizar relatórios nesta organização."

    def has_permission(self, request, view) -> bool:
        membership = _request_membership(request)
        if not has_capability(membership, "reports.view"):
            return False
        if view.__class__.__name__ == "FinancialReportView":
            return has_capability(membership, "finances.view")
        return True


class CanExportReports(BasePermission):
    message = "Você não possui permissão para exportar relatórios nesta organização."

    def has_permission(self, request, view) -> bool:
        membership = _request_membership(request)
        if not has_capability(membership, "reports.export"):
            return False
        report_type = request.query_params.get("type") or "appointments"
        if report_type == "financial":
            return has_capability(membership, "finances.view")
        return True


__all__ = ["CanExportReports", "CanViewReports"]
