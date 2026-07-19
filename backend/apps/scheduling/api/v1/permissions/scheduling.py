"""Permissões e escopo da API v1 de scheduling."""

from rest_framework.permissions import IsAuthenticated


class SchedulingAccessPermission(IsAuthenticated):
    """Restringe scheduling a terapeuta, secretária e administrador."""

    def has_permission(self, request, view):
        return super().has_permission(request, view) and (
            request.user.is_admin_role
            or request.user.is_secretary
            or request.user.is_therapist
        )

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin_role or request.user.is_secretary:
            return True
        therapist_id = getattr(obj, "therapist_id", None)
        if therapist_id is None and hasattr(obj, "appointment"):
            therapist_id = obj.appointment.therapist_id
        if therapist_id is None and hasattr(obj, "package"):
            therapist_id = obj.package.therapist_id
        return therapist_id == request.user.id


AgendaPermission = SchedulingAccessPermission

__all__ = ["AgendaPermission", "SchedulingAccessPermission"]
