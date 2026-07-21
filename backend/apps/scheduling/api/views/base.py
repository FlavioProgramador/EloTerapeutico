from apps.core.api.pagination import StandardResultsPagination
from apps.organizations.models import OrganizationMembership
from apps.scheduling.api.v1.permissions import SchedulingAccessPermission


class ScopedAgendaMixin:
    permission_classes = [SchedulingAccessPermission]
    pagination_class = StandardResultsPagination

    def scope_queryset(self, queryset, therapist_field="therapist"):
        organization = getattr(self.request, "organization", None)
        membership = getattr(self.request, "organization_membership", None)
        if organization is None or membership is None:
            return queryset.none()
        queryset = queryset.filter(organization=organization)
        if membership.role == OrganizationMembership.Role.THERAPIST:
            return queryset.filter(**{therapist_field: self.request.user})
        return queryset

    def perform_create(self, serializer):
        organization = getattr(self.request, "organization", None)
        serializer.save(organization=organization)


__all__ = ["ScopedAgendaMixin"]
