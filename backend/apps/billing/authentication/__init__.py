"""Compatibilidade para a autenticação com entitlement de billing.

Novas configurações devem usar ``apps.billing.api.authentication``.
"""

from apps.billing.api.authentication import (
    SubscriptionJWTAuthentication,
    SubscriptionRequired,
)

__all__ = ["SubscriptionJWTAuthentication", "SubscriptionRequired"]
