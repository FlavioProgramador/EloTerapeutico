"""Configuração da janela de compatibilidade do prefixo antigo de Billing."""

from __future__ import annotations

import os

from django.conf import settings

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


def legacy_billing_route_enabled() -> bool:
    """Retorna se ``/api/billing/`` deve permanecer registrado."""

    configured = getattr(settings, "BILLING_LEGACY_ROUTE_ENABLED", None)
    if configured is not None:
        return bool(configured)

    raw_value = os.getenv(
        "BILLING_LEGACY_ROUTE_ENABLED",
        "true",
    ).strip().lower()
    if raw_value in _TRUE_VALUES:
        return True
    if raw_value in _FALSE_VALUES:
        return False
    return True


__all__ = ["legacy_billing_route_enabled"]
