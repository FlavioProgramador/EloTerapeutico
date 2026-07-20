"""Integração explícita da auditoria com Django REST Framework."""

from __future__ import annotations

from rest_framework.response import Response

from apps.audit.models import AuditLog
from apps.audit.services import record_audit_event, safe_resource_repr


class AuditLogMixin:
    """Registra operações CRUD genéricas sem duplicar persistência do ViewSet."""

    audit_enabled = True
    audit_sensitive = True
    audit_action_map = {
        "retrieve": AuditLog.Action.VIEW,
        "create": AuditLog.Action.CREATE,
        "update": AuditLog.Action.UPDATE,
        "partial_update": AuditLog.Action.UPDATE,
        "destroy": AuditLog.Action.DELETE,
    }

    def _audit_is_enabled(self) -> bool:
        return bool(self.audit_enabled and self.audit_sensitive)

    def _record_instance(self, action, instance, *, on_commit: bool) -> None:
        if not self._audit_is_enabled():
            return
        record_audit_event(
            action=action,
            actor=getattr(self.request, "user", None),
            resource=instance,
            request=self.request,
            source=f"drf:{self.__class__.__name__}",
            on_commit=on_commit,
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        response = Response(serializer.data)
        if self._audit_is_enabled():
            record_audit_event(
                action=self.audit_action_map["retrieve"],
                actor=getattr(request, "user", None),
                resource=instance,
                request=request,
                source=f"drf:{self.__class__.__name__}",
                on_commit=False,
            )
        return response

    def perform_create(self, serializer):
        super().perform_create(serializer)
        self._record_instance(
            self.audit_action_map["create"], serializer.instance, on_commit=True
        )

    def perform_update(self, serializer):
        super().perform_update(serializer)
        action = self.audit_action_map.get(
            getattr(self, "action", "update"), AuditLog.Action.UPDATE
        )
        self._record_instance(action, serializer.instance, on_commit=True)

    def perform_destroy(self, instance):
        resource_label = instance._meta.label
        resource_id = instance.pk
        resource_repr = safe_resource_repr(instance)
        super().perform_destroy(instance)
        if self._audit_is_enabled():
            record_audit_event(
                action=self.audit_action_map["destroy"],
                actor=getattr(self.request, "user", None),
                resource_label=resource_label,
                resource_id=resource_id,
                resource_repr=resource_repr,
                request=self.request,
                source=f"drf:{self.__class__.__name__}",
                on_commit=True,
            )


__all__ = ["AuditLogMixin"]
