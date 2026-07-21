"""Permissões tenant-aware para relatórios e exportações."""

from rest_framework.permissions import BasePermission

from apps.organizations.permissions import has_capability


class CanViewReports(BasePermission):
    message = "Você não possui permissão para visualizar relatórios nesta organização."

    def has_permission(self, request, view) -> bool:
        membership = getattr(request, "organization_membership", None)
        if not request.user or not request.user.is_authenticated:
            return False
        if not has_capability(membership, "reports.view"):
            return False
        if view.__class__.__name__ == "FinancialReportView":
            return has_capability(membership, "finances.view")
        return True


class CanExportReports(BasePermission):
    message = "Você não possui permissão para exportar relatórios nesta organização."

    def has_permission(self, request, view) -> bool:
        membership = getattr(request, "organization_membership", None)
        if not request.user or not request.user.is_authenticated:
            return False
        if not has_capability(membership, "reports.export"):
            return False
        report_type = request.query_params.get("type") or "appointments"
        if report_type == "financial":
            return has_capability(membership, "finances.view")
        return True


__all__ = ["CanExportReports", "CanViewReports"]
