"""Permissões do módulo financeiro."""

from rest_framework.permissions import IsAuthenticated


class FinancialPermission(IsAuthenticated):
    """Permite acesso financeiro conforme papel e propriedade dos dados."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.is_admin_role or request.user.is_therapist or request.user.is_secretary

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_admin_role or user.is_secretary:
            return True
        return obj.therapist == user
