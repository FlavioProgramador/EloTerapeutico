"""Serviço canônico de escrita de eventos de auditoria."""

from __future__ import annotations

import logging
from collections.abc import Mapping

from django.contrib.contenttypes.models import ContentType
from django.db import connection, transaction

from apps.audit.exceptions import (
    AuditWriteError,
    InvalidAuditActionError,
    InvalidAuditMetadataError,
)
from apps.audit.models import AuditLog
from apps.audit.types import AuditWritePolicy, AuditWriteResult

from .request_context import extract_request_context
from .sanitization import (
    MAX_REASON_LENGTH,
    MAX_SOURCE_LENGTH,
    clean_text,
    safe_resource_repr,
    sanitize_metadata,
)

logger = logging.getLogger(__name__)


def _normalize_action(action: object) -> str:
    value = str(getattr(action, "value", action))
    if value not in AuditLog.Action.values:
        raise InvalidAuditActionError(f"Ação de auditoria inválida: {value!r}.")
    return value


def _resolve_actor(actor=None, request=None):
    candidate = actor
    if candidate is None and request is not None:
        candidate = getattr(request, "user", None)
    if candidate is not None and not getattr(candidate, "is_authenticated", False):
        return None
    return candidate


def _resolve_resource(resource=None, resource_label=None, resource_id=None):
    if resource is not None:
        content_type = ContentType.objects.get_for_model(resource, for_concrete_model=False)
        object_id = getattr(resource, "pk", None)
        if object_id is None:
            raise InvalidAuditMetadataError(
                "O recurso auditado precisa estar persistido antes do evento."
            )
        return content_type, int(object_id)
    if resource_label:
        try:
            app_label, model_name = str(resource_label).split(".", 1)
            content_type = ContentType.objects.get_by_natural_key(
                app_label.lower(), model_name.lower()
            )
        except (ValueError, ContentType.DoesNotExist) as exc:
            raise InvalidAuditMetadataError(
                "Rótulo de recurso inválido para auditoria."
            ) from exc
        return content_type, int(resource_id) if resource_id is not None else None
    return None, int(resource_id) if resource_id is not None else None


def _default_policy() -> AuditWritePolicy:
    return AuditWritePolicy(
        fail_closed_for=frozenset(),
        fail_open_for=frozenset(AuditLog.Action.values),
    )


def _handle_write_failure(
    *,
    action: str,
    source: str,
    request_id: str | None,
    policy: AuditWritePolicy,
    exc: Exception,
):
    logger.error(
        "audit_log_write_failed",
        extra={
            "action": action,
            "source": source,
            "request_id": request_id,
            "exception_type": exc.__class__.__name__,
        },
    )
    if action in policy.fail_closed_for:
        raise AuditWriteError(
            "Não foi possível registrar o evento obrigatório de auditoria."
        ) from None
    return None


def record_audit_event(
    *,
    action,
    actor=None,
    resource=None,
    resource_label: str | None = None,
    resource_id: int | None = None,
    resource_repr: str = "",
    request=None,
    metadata: Mapping[str, object] | None = None,
    reason: str | None = None,
    source: str = "application",
    on_commit: bool = True,
    policy: AuditWritePolicy | None = None,
) -> AuditWriteResult:
    """Valida, minimiza e grava um evento de auditoria.

    O schema histórico não possui colunas para ``metadata``, ``reason``,
    ``source`` ou ``request_id``. Esses valores são validados e usados na
    política/log técnico, sem serem incorporados silenciosamente a
    ``object_repr``. A persistência desses campos exige evolução aditiva futura.
    """

    normalized_action = _normalize_action(action)
    normalized_source = clean_text(source, max_length=MAX_SOURCE_LENGTH) or "application"
    clean_reason = clean_text(reason, max_length=MAX_REASON_LENGTH) if reason else None
    sanitized_metadata = sanitize_metadata(metadata)
    context = extract_request_context(request)
    resolved_actor = _resolve_actor(actor, request)
    content_type, resolved_object_id = _resolve_resource(
        resource, resource_label, resource_id
    )
    safe_repr = safe_resource_repr(resource, resource_repr)
    write_policy = policy or _default_policy()

    _ = clean_reason, sanitized_metadata

    def write_event():
        try:
            return AuditLog.objects.create(
                user=resolved_actor,
                action=normalized_action,
                ip_address=context.ip_address,
                user_agent=context.user_agent,
                content_type=content_type,
                object_id=resolved_object_id,
                object_repr=safe_repr,
            )
        except Exception as exc:
            return _handle_write_failure(
                action=normalized_action,
                source=normalized_source,
                request_id=context.request_id,
                policy=write_policy,
                exc=exc,
            )

    if on_commit and connection.in_atomic_block:
        transaction.on_commit(write_event)
        return AuditWriteResult(scheduled=True)
    return AuditWriteResult(scheduled=False, audit_log=write_event())


def log_access(
    request,
    action: str,
    obj=None,
    obj_repr: str = "",
    *,
    metadata: Mapping[str, object] | None = None,
    reason: str | None = None,
    source: str = "application",
) -> AuditWriteResult:
    """Adapter compatível para consumidores existentes."""

    normalized_action = _normalize_action(action)
    return record_audit_event(
        action=normalized_action,
        request=request,
        resource=obj,
        resource_repr=obj_repr,
        metadata=metadata,
        reason=reason,
        source=source,
        on_commit=normalized_action != AuditLog.Action.VIEW,
    )


__all__ = ["log_access", "record_audit_event"]
