"""Compatibilidade para processamento de assinaturas via webhook Asaas."""

from apps.billing.integrations.asaas.webhooks.subscriptions import (
    process_subscription_event,
)

__all__ = ["process_subscription_event"]
