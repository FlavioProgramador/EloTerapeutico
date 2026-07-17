"""Compatibilidade para a integração de webhooks do Asaas.

A implementação canônica está em ``apps.billing.integrations.asaas`` e em
``apps.billing.integrations.asaas.webhooks``.
"""

from apps.billing.integrations.asaas.client import AsaasGateway
from apps.billing.integrations.asaas.webhooks import (
    PAYMENT_STATUS_BY_EVENT,
    handle_asaas_webhook,
    process_webhook_event,
)
from apps.billing.services.subscriptions import (
    activate_subscription_from_payment,
    mark_subscription_past_due,
)

__all__ = [
    "AsaasGateway",
    "PAYMENT_STATUS_BY_EVENT",
    "activate_subscription_from_payment",
    "handle_asaas_webhook",
    "mark_subscription_past_due",
    "process_webhook_event",
]
