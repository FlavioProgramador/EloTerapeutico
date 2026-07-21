"""Permissões de scheduling baseadas na membership da organização ativa."""

from rest_framework.permissions import SAFE_METHODS, IsAuthenticated

from apps.organizations.models import OrganizationMembership
from apps.organizations.permissions import has_capability


class SchedulingAccessPermission(IsAuthenticated):
    """Aplica capacidade e vínculo do tenant no backend."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        membership = getattr(request, "organization_membership", None)
        capability = "scheduling.view" if request.method in SAFE_METHODS else "scheduling.manage"
        return has_capability(membership, capability)

    def has_object_permission(self, request, view, obj):
        membership = getattr(request, "organization_membership", None)
        organization_id = getattr(obj, "organization_id", None)
        if organization_id is None and hasattr(obj, "appointment"):
            organization_id = obj.appointment.organization_id
        if organization_id is None and hasattr(obj, "package"):
            organization_id = obj.package.organization_id
        if (
            membership is None
            or membership.status != OrganizationMembership.Status.ACTIVE
            or organization_id != membership.organization_id
        ):
            return False
        if membership.role != OrganizationMembership.Role.THERAPIST:
            return True
        therapist_id = getattr(obj, "therapist_id", None)
        if therapist_id is None and hasattr(obj, "appointment"):
            therapist_id = obj.appointment.therapist_id
        if therapist_id is None and hasattr(obj, "package"):
            therapist_id = obj.package.therapist_id
        return therapist_id == request.user.id


AgendaPermission = SchedulingAccessPermission

__all__ = ["AgendaPermission", "SchedulingAccessPermission"]
