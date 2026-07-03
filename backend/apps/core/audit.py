"""Trilha de auditoria compartilhada para dados sensíveis."""

import logging

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class AuditLog(models.Model):
    class Action(models.TextChoices):
        VIEW = "VIEW", "Visualizou"
        CREATE = "CREATE", "Criou"
        UPDATE = "UPDATE", "Atualizou"
        DELETE = "DELETE", "Deletou"
        EXPORT = "EXPORT", "Exportou"
        ANONYMIZE = "ANONYMIZE", "Anonimizou"

    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
        verbose_name="Usuário",
    )
    action = models.CharField(max_length=20, choices=Action.choices, verbose_name="Ação")
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Endereço IP",
    )
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Data/Hora")
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    object_repr = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Representação do objeto",
        help_text="Descrição legível do objeto no momento do log.",
    )

    class Meta:
        app_label = "users"
        verbose_name = "Log de Auditoria"
        verbose_name_plural = "Logs de Auditoria"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return (
            f"[{self.timestamp:%d/%m/%Y %H:%M}] "
            f"{self.user} – {self.action} – {self.object_repr}"
        )

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError(
                "Logs de auditoria são imutáveis e não podem ser alterados."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError(
            "Logs de auditoria são imutáveis e não podem ser deletados."
        )


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
