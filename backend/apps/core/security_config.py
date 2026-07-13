"""Validações puras para configurações sensíveis de produção."""

from __future__ import annotations

from collections.abc import Mapping

from django.core.exceptions import ImproperlyConfigured

_DEFAULT_FORBIDDEN_VALUES = {
    "changeme",
    "change-me",
    "change_me",
    "default",
    "development",
    "dev-secret",
    "secret",
    "test",
}


def require_strong_secret(
    name: str,
    value: object,
    *,
    min_length: int = 32,
    forbidden_values: set[str] | None = None,
) -> str:
    """Rejeita ausência, placeholders conhecidos e valores curtos."""

    normalized = str(value or "").strip()
    forbidden = _DEFAULT_FORBIDDEN_VALUES | {
        str(item).strip().lower() for item in (forbidden_values or set())
    }
    if not normalized or normalized.lower() in forbidden or len(normalized) < min_length:
        raise ImproperlyConfigured(
            f"{name} deve possuir pelo menos {min_length} caracteres e não pode usar valor padrão."
        )
    return normalized


def require_distinct_secrets(secrets_by_name: Mapping[str, object]) -> None:
    """Impede reutilização da mesma chave em finalidades criptográficas distintas."""

    normalized = {
        name: str(value or "").strip()
        for name, value in secrets_by_name.items()
    }
    names = list(normalized)
    for index, first_name in enumerate(names):
        for second_name in names[index + 1 :]:
            if normalized[first_name] and normalized[first_name] == normalized[second_name]:
                raise ImproperlyConfigured(
                    f"{first_name} e {second_name} devem usar segredos distintos."
                )
