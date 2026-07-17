"""Task periódica de reconciliação de pagamentos."""

from __future__ import annotations

import logging

from celery import shared_task
from django.conf import settings

from apps.billing.models import Payment
from apps.billing.services.payment_sync import (
    PaymentRefreshUnavailable,
    refresh_gateway_payment,
)

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.billing.tasks.reconcile_asaas_payments",
    acks_late=True,
    ignore_result=True,
    soft_time_limit=240,
    time_limit=300,
)
def reconcile_asaas_payments() -> dict[str, int]:
    """Reconcilia cobranças operacionais sem confiar no estado do frontend."""

    if not getattr(settings, "BILLING_RECONCILIATION_ENABLED", True):
        return {"checked": 0, "updated": 0, "failed": 0}

    batch_size = max(
        int(getattr(settings, "BILLING_RECONCILIATION_BATCH_SIZE", 50)),
        1,
    )
    payments = list(
        Payment.objects.filter(
            gateway_name="ASAAS",
            gateway_payment_id__isnull=False,
            status__in=[
                Payment.Status.PENDING,
                Payment.Status.AUTHORIZED,
                Payment.Status.OVERDUE,
                Payment.Status.AWAITING_RISK_ANALYSIS,
            ],
        )
        .select_related("user", "billing_order", "subscription")
        .order_by("updated_at")[:batch_size]
    )
    checked = updated = failed = 0
    for payment in payments:
        checked += 1
        previous_status = payment.status
        try:
            refreshed = refresh_gateway_payment(
                user=payment.user,
                payment_id=payment.pk,
            )
        except PaymentRefreshUnavailable:
            failed += 1
        except Exception as exc:
            failed += 1
            logger.warning(
                "billing_reconciliation_failed",
                extra={
                    "payment_id": payment.pk,
                    "exception_type": exc.__class__.__name__,
                },
            )
        else:
            if refreshed.status != previous_status:
                updated += 1
    return {"checked": checked, "updated": updated, "failed": failed}
