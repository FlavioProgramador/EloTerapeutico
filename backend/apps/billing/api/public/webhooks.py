"""Compatibilidade para a view pública do webhook Asaas.

A implementação canônica está em ``apps.billing.api.public.views.webhooks``.
"""

from .views.webhooks import AsaasWebhookView

__all__ = ["AsaasWebhookView"]
