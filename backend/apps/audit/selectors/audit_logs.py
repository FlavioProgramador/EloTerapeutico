"""Selectors somente leitura da trilha de auditoria."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.audit.models import AuditLog


def _base_queryset() -> QuerySet[AuditLog]:
    return AuditLog.objects.select_related("user", "content_type").order_by("-timestamp")


def audit_logs_accessible_to(*, user) -> QuerySet[AuditLog]:
    if not getattr(user, "is_authenticated", False):
        return AuditLog.objects.none()
    if getattr(user, "is_superuser", False) or user.has_perm("audit.view_auditlog"):
        return _base_queryset()
    return AuditLog.objects.none()


def audit_logs_for_actor(*, user, actor) -> QuerySet[AuditLog]:
    return audit_logs_accessible_to(user=user).filter(user=actor)


def audit_logs_for_resource(*, user, resource) -> QuerySet[AuditLog]:
    if getattr(resource, "pk", None) is None:
        return AuditLog.objects.none()
    return audit_logs_accessible_to(user=user).filter(
        content_type__app_label=resource._meta.app_label,
        content_type__model=resource._meta.model_name,
        object_id=resource.pk,
    )


def audit_logs_for_period(*, user, start_at, end_at) -> QuerySet[AuditLog]:
    return audit_logs_accessible_to(user=user).filter(
        timestamp__gte=start_at,
        timestamp__lte=end_at,
    )


def audit_logs_for_action(*, user, action) -> QuerySet[AuditLog]:
    return audit_logs_accessible_to(user=user).filter(
        action=str(getattr(action, "value", action))
    )


__all__ = [
    "audit_logs_accessible_to",
    "audit_logs_for_action",
    "audit_logs_for_actor",
    "audit_logs_for_period",
    "audit_logs_for_resource",
]
