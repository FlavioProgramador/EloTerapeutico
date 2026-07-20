"""Permissões da API financeira."""

from rest_framework.permissions import IsAuthenticated


class FinancesPermission(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and (
            request.user.is_admin_role
            or request.user.is_therapist
            or request.user.is_secretary
        )

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin_role or request.user.is_secretary:
            return True
        return obj.therapist_id == request.user.pk


FinancialPermission = FinancesPermission
