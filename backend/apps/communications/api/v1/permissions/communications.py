from __future__ import annotations

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from rest_framework.permissions import BasePermission


def _enforce_access(owner) -> None:
    """Resolve a fachada legada para preservar pontos de monkeypatch existentes."""

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
        return True


class _RolePermission(BasePermission):
    allowed_roles: set[str] = set()
    message = "Você não possui permissão para executar esta ação."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or request.user.role in self.allowed_roles)
        )


class CanSendCommunication(_RolePermission):
    allowed_roles = {"therapist", "secretary", "admin"}


class CanManageCommunicationTemplates(_RolePermission):
    allowed_roles = {"therapist", "admin"}


class CanManageCommunicationAutomations(_RolePermission):
    allowed_roles = {"therapist", "admin"}


class CanManageCommunicationChannels(_RolePermission):
    allowed_roles = {"therapist", "admin"}


class CanViewCommunicationLogs(_RolePermission):
    allowed_roles = {"therapist", "secretary", "admin"}


class CanRetryCommunication(_RolePermission):
    allowed_roles = {"therapist", "admin"}
