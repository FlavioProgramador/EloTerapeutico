# mypy: ignore-errors
"""Trilha de auditoria compartilhada para dados sensíveis."""

import logging

from django.contrib.contenttypes.models import ContentType

from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)


def log_access(request, action: str, obj=None, obj_repr: str = "") -> None:
    try:
        content_type = None
        object_id = None
        if obj is not None:
            content_type = ContentType.objects.get_for_model(obj)
            object_id = obj.pk

        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action=action,
            ip_address=_get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            content_type=content_type,
            object_id=object_id,
            object_repr=obj_repr or str(obj),
        )
    except Exception:
        logger.exception("Falha ao registrar log de auditoria")


def _get_client_ip(request) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class AuditLogMixin:
    audit_sensitive = True

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        if self.audit_sensitive:
            log_access(request, AuditLog.Action.VIEW, obj=self.get_object())
        return response

    def perform_create(self, serializer):
        super().perform_create(serializer)
        if self.audit_sensitive:
            log_access(
                request=self.request,
                action=AuditLog.Action.CREATE,
                obj=serializer.instance,
            )

    def perform_update(self, serializer):
        super().perform_update(serializer)
        if self.audit_sensitive:
            log_access(
                request=self.request,
                action=AuditLog.Action.UPDATE,
                obj=serializer.instance,
            )

    def perform_destroy(self, instance):
        if self.audit_sensitive:
            log_access(
                request=self.request,
                action=AuditLog.Action.DELETE,
                obj=instance,
            )
        super().perform_destroy(instance)
