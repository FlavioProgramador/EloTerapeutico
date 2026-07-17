"""Compatibilidade temporária para autenticação da API v1.

O contrato canônico está em ``apps.billing.api.authentication``.
"""

from apps.billing.api.authentication import (
    SubscriptionJWTAuthentication,
    SubscriptionRequired,
)

__all__ = ["SubscriptionJWTAuthentication", "SubscriptionRequired"]
