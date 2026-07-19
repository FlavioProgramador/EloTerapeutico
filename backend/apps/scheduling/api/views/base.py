from apps.core.api.pagination import StandardResultsPagination
from apps.scheduling.api.v1.permissions import SchedulingAccessPermission


class ScopedAgendaMixin:
    permission_classes = [SchedulingAccessPermission]
    pagination_class = StandardResultsPagination

    def scope_queryset(self, queryset, therapist_field="therapist"):
        user = self.request.user
        if user.is_admin_role or user.is_secretary:
            return queryset
        return queryset.filter(**{therapist_field: user})


__all__ = ["ScopedAgendaMixin"]
