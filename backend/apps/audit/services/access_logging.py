# mypy: ignore-errors
"""Trilha de auditoria compartilhada para dados sensíveis."""

from __future__ import annotations

import ipaddress
import logging
import re

from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
MAX_OBJECT_REPR_LENGTH = 200
MAX_USER_AGENT_LENGTH = 512


def _clean_text(value: object, *, max_length: int) -> str:
    """Normaliza texto de auditoria e limita seu tamanho.

    Remove caracteres de controle e espaços redundantes para reduzir risco de
    quebra de linha, log injection e armazenamento excessivo.

    Args:
        value: Valor que será convertido em texto.
        max_length: Quantidade máxima de caracteres preservados.

    Returns:
        Texto normalizado e truncado.
    """
    text = _CONTROL_CHARS.sub(" ", str(value or ""))
    text = " ".join(text.split())
    return text[:max_length]


def _safe_object_repr(obj=None, explicit: str = "") -> str:
    """Gera descrição mínima sem depender de ``str(obj)``.

    Métodos ``__str__`` frequentemente incluem nomes, e-mails ou trechos de
    prontuário. Quando o chamador não fornece uma descrição explícita, o log
    registra somente o rótulo técnico do modelo e sua chave primária.

    Args:
        obj: Instância opcional associada ao evento.
        explicit: Descrição segura fornecida pelo chamador.

    Returns:
        Representação sanitizada com no máximo 200 caracteres.
    """

    if explicit:
        return _clean_text(explicit, max_length=MAX_OBJECT_REPR_LENGTH)
    if obj is None:
        return ""
    model_label = getattr(getattr(obj, "_meta", None), "label", obj.__class__.__name__)
    object_id = getattr(obj, "pk", None)
    suffix = f"#{object_id}" if object_id is not None else "#sem-id"
    return _clean_text(f"{model_label}{suffix}", max_length=MAX_OBJECT_REPR_LENGTH)


def _valid_ip(value: object) -> str | None:
    """Valida e normaliza um endereço IPv4 ou IPv6.

    Args:
        value: Valor obtido dos metadados da requisição.

    Returns:
        Endereço IP normalizado ou ``None`` quando ausente ou inválido.
    """
    candidate = str(value or "").strip()
    if not candidate:
        return None
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


def _get_client_ip(request) -> str | None:
    """Obtém IP sem confiar em cabeçalhos de proxy por padrão.

    Headers encaminhados somente são considerados quando
    ``TRUST_PROXY_CLIENT_IP_HEADERS`` está habilitado para uma infraestrutura
    de proxy conhecida e controlada.

    Args:
        request: Requisição Django contendo os metadados de rede.

    Returns:
        IP validado do cliente ou ``None``.
    """

    if getattr(settings, "TRUST_PROXY_CLIENT_IP_HEADERS", False):
        azure_client_ip = _valid_ip(request.META.get("HTTP_X_AZURE_CLIENTIP"))
        if azure_client_ip:
            return azure_client_ip

        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded_for:
            forwarded_ip = _valid_ip(forwarded_for.split(",", 1)[0])
            if forwarded_ip:
                return forwarded_ip

    return _valid_ip(request.META.get("REMOTE_ADDR"))


def log_access(request, action: str, obj=None, obj_repr: str = "") -> None:
    """Registra uma ação sensível sem interromper a operação principal.

    O serviço persiste usuário, ação, IP validado, user agent sanitizado e uma
    representação mínima do objeto. Qualquer falha de auditoria é registrada
    de forma sanitizada e não é propagada ao fluxo HTTP.

    Args:
        request: Requisição Django associada ao evento.
        action: Ação definida por ``AuditLog.Action``.
        obj: Objeto opcional relacionado ao acesso.
        obj_repr: Descrição explícita e segura do objeto.

    Returns:
        ``None``.

    Side Effects:
        Cria um ``AuditLog``. Em falha, escreve apenas o tipo da exceção no
        logger da aplicação.
    """
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
            user_agent=_clean_text(
                request.META.get("HTTP_USER_AGENT", ""),
                max_length=MAX_USER_AGENT_LENGTH,
            ),
            content_type=content_type,
            object_id=object_id,
            object_repr=_safe_object_repr(obj, obj_repr),
        )
    except Exception as exc:
        logger.error(
            "audit_log_write_failed",
            extra={"exception_type": exc.__class__.__name__},
        )


class AuditLogMixin:
    """Adiciona auditoria automática às operações sensíveis de ViewSets.

    O mixin registra leitura, criação, atualização e exclusão após ou antes do
    hook correspondente do DRF, sem alterar a resposta do endpoint. A auditoria
    pode ser desativada por classe com ``audit_sensitive = False``.
    """

    audit_sensitive = True

    def retrieve(self, request, *args, **kwargs):
        """Registra visualização após recuperar o objeto com sucesso."""
        response = super().retrieve(request, *args, **kwargs)
        if self.audit_sensitive:
            log_access(request, AuditLog.Action.VIEW, obj=self.get_object())
        return response

    def perform_create(self, serializer):
        """Registra a criação depois que o serializer persiste a instância."""
        super().perform_create(serializer)
        if self.audit_sensitive:
            log_access(
                request=self.request,
                action=AuditLog.Action.CREATE,
                obj=serializer.instance,
            )

    def perform_update(self, serializer):
        """Registra a atualização depois que o serializer persiste a instância."""
        super().perform_update(serializer)
        if self.audit_sensitive:
            log_access(
                request=self.request,
                action=AuditLog.Action.UPDATE,
                obj=serializer.instance,
            )

    def perform_destroy(self, instance):
        """Registra a exclusão antes de delegar a remoção ao ViewSet."""
        if self.audit_sensitive:
            log_access(
                request=self.request,
                action=AuditLog.Action.DELETE,
                obj=instance,
            )
        super().perform_destroy(instance)
