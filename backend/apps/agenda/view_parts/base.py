from rest_framework.permissions import IsAuthenticated

from core.pagination import StandardResultsPagination


class AgendaPermission(IsAuthenticated):
    """Restringe a agenda a terapeuta, secretária e administrador."""

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


class ScopedAgendaMixin:
    permission_classes = [AgendaPermission]
    pagination_class = StandardResultsPagination

    def scope_queryset(self, queryset, therapist_field="therapist"):
        user = self.request.user
        if user.is_admin_role or user.is_secretary:
            return queryset
        return queryset.filter(**{therapist_field: user})
