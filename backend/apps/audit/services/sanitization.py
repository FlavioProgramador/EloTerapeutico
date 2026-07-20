"""Minimização e sanitização dos dados auditáveis."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any

from apps.audit.exceptions import InvalidAuditMetadataError

_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
MAX_OBJECT_REPR_LENGTH = 200
MAX_USER_AGENT_LENGTH = 512
MAX_REASON_LENGTH = 200
MAX_SOURCE_LENGTH = 80
MAX_METADATA_DEPTH = 3
MAX_METADATA_ITEMS = 32
MAX_METADATA_TEXT_LENGTH = 200

_SENSITIVE_KEYS = {
    "access",
    "api_key",
    "authorization",
    "clinical_notes",
    "cookie",
    "cpf",
    "document",
    "medical_record",
    "password",
    "password1",
    "password2",
    "refresh",
    "secret",
    "signature",
    "token",
}


def clean_text(value: object, *, max_length: int) -> str:
    text = _CONTROL_CHARS.sub(" ", str(value or ""))
    text = " ".join(text.split())
    return text[:max_length]


def safe_resource_repr(resource=None, explicit: str = "") -> str:
    if explicit:
        return clean_text(explicit, max_length=MAX_OBJECT_REPR_LENGTH)
    if resource is None:
        return ""
    model_label = getattr(getattr(resource, "_meta", None), "label", None)
    if not model_label:
        model_label = resource.__class__.__name__
    object_id = getattr(resource, "pk", None)
    suffix = f"#{object_id}" if object_id is not None else "#sem-id"
    return clean_text(
        f"{model_label}{suffix}", max_length=MAX_OBJECT_REPR_LENGTH
    )


def _is_sensitive_key(key: object) -> bool:
    normalized = str(key).strip().lower().replace("-", "_")
    return normalized in _SENSITIVE_KEYS or any(
        token in normalized
        for token in ("password", "token", "secret", "authorization", "cookie")
    )


def _sanitize_value(value: Any, *, depth: int) -> object:
    if depth > MAX_METADATA_DEPTH:
        raise InvalidAuditMetadataError(
            "Metadados de auditoria excedem a profundidade permitida."
        )
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, str):
        return clean_text(value, max_length=MAX_METADATA_TEXT_LENGTH)
    if isinstance(value, Mapping):
        return sanitize_metadata(value, depth=depth + 1)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return [
            _sanitize_value(item, depth=depth + 1)
            for item in list(value)[:MAX_METADATA_ITEMS]
        ]
    raise InvalidAuditMetadataError(
        f"Tipo de metadado não permitido: {value.__class__.__name__}."
    )


def sanitize_metadata(
    metadata: Mapping[str, object] | None,
    *,
    depth: int = 0,
) -> dict[str, object]:
    if metadata is None:
        return {}
    if not isinstance(metadata, Mapping):
        raise InvalidAuditMetadataError(
            "Metadados de auditoria devem ser um mapeamento."
        )
    sanitized: dict[str, object] = {}
    for key, value in list(metadata.items())[:MAX_METADATA_ITEMS]:
        key_text = clean_text(key, max_length=80)
        if not key_text or _is_sensitive_key(key_text):
            continue
        sanitized[key_text] = _sanitize_value(value, depth=depth)
    return sanitized


__all__ = [
    "MAX_OBJECT_REPR_LENGTH",
    "MAX_REASON_LENGTH",
    "MAX_SOURCE_LENGTH",
    "MAX_USER_AGENT_LENGTH",
    "clean_text",
    "safe_resource_repr",
    "sanitize_metadata",
]
