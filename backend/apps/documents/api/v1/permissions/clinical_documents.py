"""Permissões específicas de documentos clínicos por organização."""

from rest_framework.permissions import BasePermission

from apps.organizations.permissions import has_capability
from apps.organizations.services.tenant_context import ensure_request_organization

READ_ACTIONS = {
    "list",
    "retrieve",
    "preview",
    "download",
    "rendered_content",
}


class IsClinicalDocumentUser(BasePermission):
    """Aplica capabilities documentais da membership ativa."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        _, membership = ensure_request_organization(request=request, required=True)
        action = getattr(view, "action", None)
        read_only = request.method in {"GET", "HEAD", "OPTIONS"} or action in READ_ACTIONS
        return has_capability(
            membership,
            "documents.view" if read_only else "documents.manage",
        )

    def has_object_permission(self, request, view, obj):
        organization, membership = ensure_request_organization(
            request=request,
            required=True,
        )
        object_organization_id = getattr(obj, "organization_id", None)
        if object_organization_id is not None and object_organization_id != organization.pk:
            return False
        action = getattr(view, "action", None)
        read_only = request.method in {"GET", "HEAD", "OPTIONS"} or action in READ_ACTIONS
        return has_capability(
            membership,
            "documents.view" if read_only else "documents.manage",
        )
