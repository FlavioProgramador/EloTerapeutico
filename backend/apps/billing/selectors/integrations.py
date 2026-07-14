from typing import Any

from apps.billing.models import WebhookEvent


def get_webhook_delivery_stats() -> dict[str, Any]:
    last_event = WebhookEvent.objects.order_by("-received_at").first()
    return {
        "last_webhook_at": last_event.received_at if last_event else None,
        "pending_events": WebhookEvent.objects.filter(
            status__in=[WebhookEvent.Status.RECEIVED, WebhookEvent.Status.RETRY]
        ).count(),
        "failed_events": WebhookEvent.objects.filter(
            status=WebhookEvent.Status.FAILED
        ).count(),
    }
