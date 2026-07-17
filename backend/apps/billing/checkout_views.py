"""Compatibilidade para os endpoints históricos de checkout.

Novos imports devem utilizar ``apps.billing.api.v1.views``.
"""

from .api.v1.views.checkout import CheckoutCreateView
from .api.v1.views.health import BillingIntegrationHealthView

__all__ = ["BillingIntegrationHealthView", "CheckoutCreateView"]
