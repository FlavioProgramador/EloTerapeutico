"""Controles de segurança compartilhados pelo domínio de billing."""

from __future__ import annotations

import re
from typing import Any

REDACTED_VALUE = "[REDACTED]"

# As chaves são normalizadas removendo pontuação e convertendo para minúsculas.
# A lista é deliberadamente conservadora para evitar persistir credenciais,
# documentos fiscais e dados de pagamento em JSONs de auditoria/diagnóstico.
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
    """Cria uma cópia recursiva de ``value`` com campos sensíveis mascarados.

    O objeto recebido não é alterado, permitindo que o payload original continue
    disponível somente durante o processamento em memória.
    """

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
