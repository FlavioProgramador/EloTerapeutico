from __future__ import annotations

from django.utils import timezone

from apps.billing.models import Payment, Subscription
from apps.billing.services.orders import upsert_gateway_payment

from .constants import PAYMENT_STATUS_BY_EVENT
from .orders import (
    find_order,
    subscription_for_order,
    update_order_financial_status,
)


def process_payment_event(event_type: str, payment_data: dict) -> str:
    order = find_order(payment_data)
    if not order:
        return "retry: contratação local ainda não localizada"

    subscription = subscription_for_order(order, payment_data)
    normalized = dict(payment_data)
    normalized["status"] = PAYMENT_STATUS_BY_EVENT.get(
        event_type,
        payment_data.get("status") or Payment.Status.PENDING,
    )
    payment = upsert_gateway_payment(
        order=order,
        payload=normalized,
        subscription=subscription,
        installment_count=order.installment_count,
    )
    update_order_financial_status(order)

    # A resolução pela fachada preserva os pontos de monkeypatch históricos
    # usados pelos testes e por extensões internas do projeto.
    from apps.billing.webhooks import asaas as compatibility_webhook

    if subscription and event_type in {
        "PAYMENT_CONFIRMED",
        "PAYMENT_RECEIVED",
        "PAYMENT_APPROVED_BY_RISK_ANALYSIS",
    }:
        compatibility_webhook.activate_subscription_from_payment(
            subscription,
            payment,
        )
    elif subscription and event_type == "PAYMENT_OVERDUE":
        compatibility_webhook.mark_subscription_past_due(subscription)
    elif subscription and event_type in {
        "PAYMENT_CHARGEBACK_REQUESTED",
        "PAYMENT_REPROVED_BY_RISK_ANALYSIS",
    }:
        subscription.status = Subscription.Status.SUSPENDED
        subscription.suspended_at = timezone.now()
        subscription.save(
            update_fields=["status", "suspended_at", "updated_at"]
        )
    return "processed"
