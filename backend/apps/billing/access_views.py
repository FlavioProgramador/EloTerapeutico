"""Compatibilidade para o endpoint de entitlement.

Novos imports devem utilizar ``apps.billing.api.v1.views.entitlements``.
"""

from .api.v1.views.entitlements import EntitlementStatusView

__all__ = ["EntitlementStatusView"]
