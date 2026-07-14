"""Permissões de acesso a templates de evolução clínica."""

from rest_framework.permissions import SAFE_METHODS, IsAuthenticated


def can_access_clinical_template(*, user, template, write: bool = False) -> bool:
    if user.is_secretary or template.owner_id not in (None, user.id):
        return False
    if not write or template.owner_id == user.id:
        return True
    return user.has_perm("records.manage_system_clinical_templates")


class CanAccessClinicalTemplates(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and not request.user.is_secretary

    def has_object_permission(self, request, view, obj):
        return can_access_clinical_template(
            user=request.user,
            template=obj,
            write=request.method not in SAFE_METHODS,
        )
