from __future__ import annotations

from django.utils import timezone

from apps.billing.models import BillingOrder, Subscription
from apps.billing.security import redact_sensitive_data


def process_subscription_event(
    event_type: str,
    subscription_data: dict,
) -> str:
    gateway_subscription_id = subscription_data.get("id")
    if not gateway_subscription_id:
        return "ignored: evento de assinatura sem identificador"

    subscription = Subscription.objects.filter(
        gateway_subscription_id=gateway_subscription_id
    ).first()
    if not subscription:
        order = BillingOrder.objects.filter(
            gateway_subscription_id=gateway_subscription_id
        ).first()
        subscription = (
            Subscription.objects.filter(billing_order=order)
            .order_by("-created_at")
            .first()
            if order
            else None
        )
    if not subscription:
        return "retry: assinatura local ainda não localizada"

    subscription.gateway_status = subscription_data.get(
        "status",
        subscription.gateway_status,
    )
    subscription.metadata = {
        **(subscription.metadata or {}),
        "last_subscription_webhook": redact_sensitive_data(
            subscription_data
        ),
    }
    update_fields = ["gateway_status", "metadata", "updated_at"]
    if event_type == "SUBSCRIPTION_DELETED":
        subscription.status = Subscription.Status.CANCELED
        subscription.canceled_at = timezone.now()
        subscription.cancel_at_period_end = False
        update_fields += [
            "status",
            "canceled_at",
            "cancel_at_period_end",
        ]
    subscription.save(update_fields=update_fields)
    return "processed"
