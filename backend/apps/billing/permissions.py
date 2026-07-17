"""Compatibilidade para imports antigos de permissões de billing."""

from .api.v1.permissions import RequireActiveSubscription, RequireFeature

__all__ = ["RequireActiveSubscription", "RequireFeature"]
