from __future__ import annotations

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from rest_framework.permissions import BasePermission

from apps.organizations.permissions import has_capability
from apps.organizations.services.tenant_context import ensure_request_organization


def _enforce_access(owner) -> None:
    """Preserva a validação de entitlement do plano."""

    from apps.communications import permissions as compatibility_permissions

    compatibility_permissions.enforce_communication_access(owner)


class CanAccessCommunications(BasePermission):
    message = "Seu plano atual não inclui o módulo de Comunicações."

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            _enforce_access(request.user)
        except DjangoPermissionDenied as exc:
            self.message = str(exc)
            return False
        _, membership = ensure_request_organization(request=request, required=True)
        return has_capability(membership, "communications.view")


class _CapabilityPermission(BasePermission):
    capability = "communications.manage"
    message = "Você não possui permissão para executar esta ação."

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        _, membership = ensure_request_organization(request=request, required=True)
        return has_capability(membership, self.capability)

    def has_object_permission(self, request, view, obj) -> bool:
        organization, membership = ensure_request_organization(
            request=request,
            required=True,
        )
        object_organization_id = getattr(obj, "organization_id", None)
        if object_organization_id is not None and object_organization_id != organization.pk:
            return False
        return has_capability(membership, self.capability)


class CanSendCommunication(_CapabilityPermission):
    pass


class CanManageCommunicationTemplates(_CapabilityPermission):
    pass


class CanManageCommunicationAutomations(_CapabilityPermission):
    pass


class CanManageCommunicationChannels(_CapabilityPermission):
    pass


class CanViewCommunicationLogs(_CapabilityPermission):
    capability = "communications.view"


class CanRetryCommunication(_CapabilityPermission):
    pass
