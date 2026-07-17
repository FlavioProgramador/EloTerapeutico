"""Compatibilidade para a autenticação com entitlement de billing."""

from apps.billing.api.v1.authentication import (
    SubscriptionJWTAuthentication,
    SubscriptionRequired,
)

__all__ = ["SubscriptionJWTAuthentication", "SubscriptionRequired"]
