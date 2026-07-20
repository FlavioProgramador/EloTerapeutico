"""Integração read-only da auditoria com Django Admin."""

from __future__ import annotations

from apps.audit.models import AuditLog
from apps.audit.services import record_audit_event


class AuditReadOnlyAdminMixin:
    """Restringe o Admin a usuários com permissão explícita de visualização."""

    def has_module_permission(self, request):
        user = request.user
        return bool(
            getattr(user, "is_authenticated", False)
            and (
                getattr(user, "is_superuser", False)
                or user.has_perm("audit.view_auditlog")
            )
        )

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if getattr(response, "status_code", 500) < 400:
            record_audit_event(
                action=AuditLog.Action.VIEW,
                actor=request.user,
                resource_label="audit.AuditLog",
                resource_repr="audit.AuditLog:list",
                request=request,
                source="django_admin",
                on_commit=False,
            )
        return response

    def change_view(self, request, object_id, form_url="", extra_context=None):
        response = super().change_view(
            request,
            object_id,
            form_url=form_url,
            extra_context=extra_context,
        )
        if getattr(response, "status_code", 500) < 400:
            record_audit_event(
                action=AuditLog.Action.VIEW,
                actor=request.user,
                resource_label="audit.AuditLog",
                resource_id=int(object_id),
                resource_repr=f"audit.AuditLog#{object_id}",
                request=request,
                source="django_admin",
                on_commit=False,
            )
        return response


__all__ = ["AuditReadOnlyAdminMixin"]
