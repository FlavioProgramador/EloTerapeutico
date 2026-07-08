"""Permissões HTTP do módulo de pacientes."""

from rest_framework.permissions import IsAuthenticated

from apps.patients.services.access_control import can_manage_patient


class PatientPermission(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        user = request.user
        if user.is_admin_role or user.is_therapist:
            return True
        return user.is_secretary and request.method in ("GET", "HEAD", "OPTIONS", "POST")

    def has_object_permission(self, request, view, obj):
        if request.user.is_secretary:
            return request.method in ("GET", "HEAD", "OPTIONS")
        return can_manage_patient(request.user, obj)
