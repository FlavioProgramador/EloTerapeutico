"""Controles de segurança compartilhados pelo domínio de billing."""

from __future__ import annotations

import re
from typing import Any

REDACTED_VALUE = "[REDACTED]"

_SENSITIVE_KEYS = frozenset(
    {
        "accesstoken",
        "apikey",
        "authorization",
        "cardnumber",
        "ccv",
        "cnpj",
        "cpf",
        "cpfcnpj",
        "creditcard",
        "creditcardnumber",
        "creditcardtoken",
        "cvv",
        "holderinfo",
        "password",
        "pixcopypaste",
        "pixqrcode",
        "refreshtoken",
        "secret",
        "token",
        "webhooktoken",
    }
)


def _normalize_key(key: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def redact_sensitive_data(value: Any) -> Any:
    """Retorna uma cópia recursiva com campos sensíveis mascarados."""

    if isinstance(value, dict):
        sanitized: dict[Any, Any] = {}
        for key, item in value.items():
            if _normalize_key(key) in _SENSITIVE_KEYS and item not in (None, ""):
                sanitized[key] = REDACTED_VALUE
            else:
                sanitized[key] = redact_sensitive_data(item)
        return sanitized

    if isinstance(value, list):
        return [redact_sensitive_data(item) for item in value]

    if isinstance(value, tuple):
        return tuple(redact_sensitive_data(item) for item in value)

    return value


__all__ = ["REDACTED_VALUE", "redact_sensitive_data"]
