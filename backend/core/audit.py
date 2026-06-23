"""
core/audit.py
Sistema de trilha de auditoria (Audit Trail) para conformidade com LGPD.
Registra automaticamente quem leu, criou ou modificou dados sensíveis.
"""

import logging

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class AuditLog(models.Model):
    """
    Registro imutável de acesso ou modificação de dados sensíveis.
    Uma vez criado, não pode ser alterado ou deletado pela aplicação.
    """

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
    action = models.CharField(
        max_length=20,
        choices=Action.choices,
        verbose_name="Ação",
    )
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name="Endereço IP"
    )
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Data/Hora")

    # Referência genérica ao objeto afetado (prontuário, paciente, etc.)
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
        return f"[{self.timestamp:%d/%m/%Y %H:%M}] {self.user} – {self.action} – {self.object_repr}"

    # Impede edição após criação
    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("Logs de auditoria são imutáveis e não podem ser alterados.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Logs de auditoria são imutáveis e não podem ser deletados.")


def log_access(request, action: str, obj=None, obj_repr: str = "") -> None:
    """
    Utilitário para registrar um log de auditoria a partir de uma view.

    Uso:
        log_access(request, AuditLog.Action.VIEW, obj=evolution, obj_repr=str(evolution))
    """
    try:
        content_type = None
        object_id = None
        if obj is not None:
            content_type = ContentType.objects.get_for_model(obj)
            object_id = obj.pk

        ip = _get_client_ip(request)

        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action=action,
            ip_address=ip,
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            content_type=content_type,
            object_id=object_id,
            object_repr=obj_repr or str(obj),
        )
    except Exception as e:
        # Nunca deixar a falha de log derrubar a requisição principal
        logger.error("Falha ao registrar log de auditoria: %s", e)


def _get_client_ip(request) -> str:
    """Extrai o IP real do cliente considerando proxies reversos."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class AuditLogMixin:
    """
    Mixin para ViewSets DRF que registra automaticamente logs de auditoria
    nas ações de leitura e escrita de dados sensíveis.

    Uso:
        class EvolutionViewSet(AuditLogMixin, viewsets.ModelViewSet):
            ...
    """

    audit_sensitive = True  # Sobrescreva para False em ViewSets não sensíveis

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        if self.audit_sensitive:
            obj = self.get_object()
            log_access(request, AuditLog.Action.VIEW, obj=obj)
        return response

    def perform_create(self, serializer):
        super().perform_create(serializer)
        if self.audit_sensitive:
            log_access(request=self.request, action=AuditLog.Action.CREATE, obj=serializer.instance)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        if self.audit_sensitive:
            log_access(request=self.request, action=AuditLog.Action.UPDATE, obj=serializer.instance)
