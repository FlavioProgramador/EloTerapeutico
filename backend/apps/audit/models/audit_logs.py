"""Modelo append-only da trilha de auditoria."""

from __future__ import annotations

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from apps.audit.exceptions import AuditLogImmutableError

from .querysets import AuditLogManager


class AuditLog(models.Model):
    """Evidência imutável de uma operação sensível concluída ou observada."""

    class Action(models.TextChoices):
        VIEW = "VIEW", "Visualizou"
        CREATE = "CREATE", "Criou"
        UPDATE = "UPDATE", "Atualizou"
        DELETE = "DELETE", "Deletou"
        EXPORT = "EXPORT", "Exportou"
        ANONYMIZE = "ANONYMIZE", "Anonimizou"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="Organização",
    )
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
    )

    objects = AuditLogManager()

    class Meta:
        db_table = "users_auditlog"
        verbose_name = "Log de Auditoria"
        verbose_name_plural = "Logs de Auditoria"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["organization", "timestamp"], name="audit_org_timestamp_idx"),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self) -> str:
        return f"[{self.timestamp:%d/%m/%Y %H:%M}] {self.action} - {self.object_repr}"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise AuditLogImmutableError(
                "Logs de auditoria são append-only e não podem ser alterados."
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise AuditLogImmutableError(
            "Logs de auditoria são append-only e não podem ser removidos."
        )


__all__ = ["AuditLog"]
