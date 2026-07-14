import hashlib
import json
import logging
import os
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from apps.billing.infrastructure.payments.asaas.client import AsaasGateway
from apps.billing.models import BillingOrder, Payment, PlanPrice, Subscription, WebhookEvent
from apps.billing.security import redact_sensitive_data
from apps.billing.services.orders import upsert_gateway_payment
from apps.billing.services.subscriptions import (
    activate_subscription_from_payment,
    mark_subscription_past_due,
)

logger = logging.getLogger(__name__)

PAYMENT_STATUS_BY_EVENT = {
    "PAYMENT_CREATED": Payment.Status.PENDING,
    "PAYMENT_UPDATED": Payment.Status.PENDING,
    "PAYMENT_AUTHORIZED": Payment.Status.AUTHORIZED,
    "PAYMENT_CONFIRMED": Payment.Status.CONFIRMED,
    "PAYMENT_RECEIVED": Payment.Status.RECEIVED,
    "PAYMENT_OVERDUE": Payment.Status.OVERDUE,
    "PAYMENT_DELETED": Payment.Status.CANCELED,
    "PAYMENT_REFUNDED": Payment.Status.REFUNDED,
    "PAYMENT_PARTIALLY_REFUNDED": Payment.Status.PARTIALLY_REFUNDED,
    "PAYMENT_REFUND_IN_PROGRESS": Payment.Status.REFUND_IN_PROGRESS,
    "PAYMENT_CHARGEBACK_REQUESTED": Payment.Status.CHARGEBACK,
    "PAYMENT_CHARGEBACK_DISPUTE": Payment.Status.CHARGEBACK_DISPUTE,
    "PAYMENT_RESTORED": Payment.Status.RESTORED,
    "PAYMENT_AWAITING_RISK_ANALYSIS": Payment.Status.AWAITING_RISK_ANALYSIS,
    "PAYMENT_APPROVED_BY_RISK_ANALYSIS": Payment.Status.CONFIRMED,
    "PAYMENT_REPROVED_BY_RISK_ANALYSIS": Payment.Status.FAILED,
}


def _payload_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _event_id(payload: dict) -> str | None:
    explicit_id = payload.get("id") or payload.get("eventId")
    if explicit_id:
        return str(explicit_id)
    event_type = payload.get("event", "UNKNOWN")
    payment = payload.get("payment") or {}
    subscription = payload.get("subscription") or {}
    related_id = payment.get("id") or subscription.get("id")
    return f"{event_type}:{related_id}" if related_id else None


def _legacy_order_for_subscription(gateway_subscription_id: str) -> BillingOrder | None:
    if not gateway_subscription_id:
        return None
    subscription = (
        Subscription.objects.select_related("plan", "billing_order")
        .filter(gateway_subscription_id=gateway_subscription_id)
        .first()
    )
    if not subscription:
        return None
    if subscription.billing_order_id:
        return subscription.billing_order

    plan = subscription.plan
    interval = (
        PlanPrice.BillingInterval.YEARLY
        if plan.billing_cycle == "YEARLY"
        else PlanPrice.BillingInterval.MONTHLY
    )
    price, _ = PlanPrice.objects.get_or_create(
        slug=f"{plan.slug}-{interval.lower()}-recurring-webhook-legacy",
        defaults={
            "plan": plan,
            "name": f"{plan.name} — {'Anual' if interval == 'YEARLY' else 'Mensal'}",
            "currency": plan.currency,
            "total_amount": plan.price,
            "billing_interval": interval,
            "billing_model": PlanPrice.BillingModel.RECURRING,
            "discount_percentage": Decimal("0.00"),
            "installments_enabled": False,
            "min_installments": 1,
            "max_installments": 1,
            "is_active": plan.is_active,
        },
    )
    external_reference = f"legacy-webhook-subscription-{subscription.pk}"
    order, _ = BillingOrder.objects.get_or_create(
        external_reference=external_reference,
        defaults={
            "user": subscription.user,
            "plan": plan,
            "plan_price": price,
            "status": BillingOrder.Status.PENDING,
            "billing_model": price.billing_model,
            "billing_interval": price.billing_interval,
            "currency": price.currency,
            "total_amount": price.total_amount,
            "discount_amount": Decimal("0.00"),
            "installment_count": 1,
            "installment_amount_estimate": price.total_amount,
            "gateway_name": subscription.gateway_name,
            "gateway_customer_id": subscription.gateway_customer_id,
            "gateway_subscription_id": gateway_subscription_id,
            "idempotency_key": external_reference,
            "commercial_snapshot": {
                "legacy": True,
                "plan_name": plan.name,
                "total_amount": str(price.total_amount),
            },
            "metadata": {"origin": "legacy_webhook_compatibility"},
        },
    )
    if not subscription.billing_order_id:
        subscription.billing_order = order
        subscription.save(update_fields=["billing_order", "updated_at"])
    Payment.objects.filter(subscription=subscription, billing_order__isnull=True).update(
        billing_order=order
    )
    return order


def _find_order(payment_data: dict) -> BillingOrder | None:
    payment_id = payment_data.get("id")
    if payment_id:
        existing = (
            Payment.objects.select_related("billing_order")
            .filter(gateway_payment_id=payment_id)
            .first()
        )
        if existing and existing.billing_order_id:
            return existing.billing_order

    gateway_subscription_id = payment_data.get("subscription")
    query = Q()
    if gateway_subscription_id:
        query |= Q(gateway_subscription_id=gateway_subscription_id)
    if payment_data.get("installment"):
        query |= Q(gateway_installment_id=payment_data["installment"])
    if payment_data.get("externalReference"):
        query |= Q(external_reference=payment_data["externalReference"])

    order = None
    if query:
        order = (
            BillingOrder.objects.select_related("plan", "plan_price", "user")
            .filter(query)
            .order_by("-created_at")
            .first()
        )
    return order or _legacy_order_for_subscription(gateway_subscription_id)


def _subscription_for_order(order: BillingOrder, payment_data: dict) -> Subscription | None:
    subscription = order.subscriptions.order_by("-created_at").first()
    if subscription:
        return subscription
    gateway_subscription_id = payment_data.get("subscription")
    if gateway_subscription_id:
        return Subscription.objects.filter(
            gateway_subscription_id=gateway_subscription_id
        ).first()
    source_id = (order.metadata or {}).get("plan_change_from_subscription_id")
    return Subscription.objects.filter(pk=source_id).first() if source_id else None


def _update_order_financial_status(order: BillingOrder) -> None:
    payments = order.payments.all()
    total = payments.count()
    paid = payments.filter(
        status__in=[Payment.Status.CONFIRMED, Payment.Status.RECEIVED]
    ).count()
    overdue = payments.filter(status=Payment.Status.OVERDUE).exists()
    chargeback = payments.filter(status=Payment.Status.CHARGEBACK).exists()
    refunded = payments.filter(status=Payment.Status.REFUNDED).count()

    if chargeback:
        next_status = BillingOrder.Status.CHARGEBACK
    elif total and refunded == total:
        next_status = BillingOrder.Status.REFUNDED
    elif refunded:
        next_status = BillingOrder.Status.PARTIALLY_REFUNDED
    elif total and paid == total:
        next_status = BillingOrder.Status.PAID
    elif paid:
        next_status = BillingOrder.Status.PARTIALLY_PAID
    elif overdue:
        next_status = BillingOrder.Status.OVERDUE
    else:
        next_status = BillingOrder.Status.PENDING

    if order.status != next_status:
        order.status = next_status
        update_fields = ["status", "updated_at"]
        if (
            next_status in {BillingOrder.Status.PAID, BillingOrder.Status.PARTIALLY_PAID}
            and not order.confirmed_at
        ):
            order.confirmed_at = timezone.now()
            update_fields.append("confirmed_at")
        order.save(update_fields=update_fields)


def _process_payment_event(event_type: str, payment_data: dict) -> str:
    order = _find_order(payment_data)
    if not order:
        return "retry: contratação local ainda não localizada"
    subscription = _subscription_for_order(order, payment_data)
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
    _update_order_financial_status(order)

    if subscription and event_type in {
        "PAYMENT_CONFIRMED",
        "PAYMENT_RECEIVED",
        "PAYMENT_APPROVED_BY_RISK_ANALYSIS",
    }:
        activate_subscription_from_payment(subscription, payment)
    elif subscription and event_type == "PAYMENT_OVERDUE":
        mark_subscription_past_due(subscription)
    elif subscription and event_type in {
        "PAYMENT_CHARGEBACK_REQUESTED",
        "PAYMENT_REPROVED_BY_RISK_ANALYSIS",
    }:
        subscription.status = Subscription.Status.SUSPENDED
        subscription.suspended_at = timezone.now()
        subscription.save(update_fields=["status", "suspended_at", "updated_at"])
    return "processed"


def _process_subscription_event(event_type: str, subscription_data: dict) -> str:
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
        subscription = order.subscriptions.order_by("-created_at").first() if order else None
    if not subscription:
        return "retry: assinatura local ainda não localizada"

    subscription.gateway_status = subscription_data.get(
        "status", subscription.gateway_status
    )
    subscription.metadata = {
        **(subscription.metadata or {}),
        "last_subscription_webhook": redact_sensitive_data(subscription_data),
    }
    update_fields = ["gateway_status", "metadata", "updated_at"]
    if event_type == "SUBSCRIPTION_DELETED":
        subscription.status = Subscription.Status.CANCELED
        subscription.canceled_at = timezone.now()
        subscription.cancel_at_period_end = False
        update_fields += ["status", "canceled_at", "cancel_at_period_end"]
    subscription.save(update_fields=update_fields)
    return "processed"


def _persist_webhook_event(
    *,
    payload: dict,
    event_type: str,
    event_hash: str,
    event_identifier: str | None,
) -> WebhookEvent:
    defaults = {
        "gateway_name": "ASAAS",
        "event_type": event_type,
        "payload": redact_sensitive_data(payload),
        "status": WebhookEvent.Status.RECEIVED,
    }
    if event_identifier:
        lookup = {"event_id": event_identifier}
        defaults["payload_hash"] = event_hash
    else:
        lookup = {"payload_hash": event_hash}
        defaults["event_id"] = None
    try:
        with transaction.atomic():
            webhook_event, _ = WebhookEvent.objects.get_or_create(
                **lookup,
                defaults=defaults,
            )
            return webhook_event
    except IntegrityError:
        query = Q(payload_hash=event_hash)
        if event_identifier:
            query |= Q(event_id=event_identifier)
        return WebhookEvent.objects.get(query)


def _finish_event(event_id: int, result: str, max_retries: int) -> WebhookEvent:
    with transaction.atomic():
        locked = WebhookEvent.objects.select_for_update().get(pk=event_id)
        if result.startswith("retry:"):
            locked.status = (
                WebhookEvent.Status.FAILED
                if locked.attempt_count >= max_retries
                else WebhookEvent.Status.RETRY
            )
            locked.next_retry_at = (
                None
                if locked.status == WebhookEvent.Status.FAILED
                else timezone.now() + timedelta(minutes=min(2**locked.attempt_count, 60))
            )
            locked.last_error = result.removeprefix("retry: ")
            locked.error_message = locked.last_error
            locked.processed = False
            locked.processed_at = None
        elif result.startswith("ignored:"):
            locked.status = WebhookEvent.Status.IGNORED
            locked.last_error = result.removeprefix("ignored: ")
            locked.error_message = locked.last_error
            locked.processed = True
            locked.processed_at = timezone.now()
            locked.next_retry_at = None
        else:
            locked.status = WebhookEvent.Status.PROCESSED
            locked.last_error = ""
            locked.error_message = ""
            locked.processed = True
            locked.processed_at = timezone.now()
            locked.next_retry_at = None
        locked.save(
            update_fields=[
                "status",
                "next_retry_at",
                "last_error",
                "error_message",
                "processed",
                "processed_at",
                "updated_at",
            ]
        )
        return locked


def _hydrate_payment_for_worker(payload: dict) -> dict:
    payment_data = dict(payload.get("payment") or {})
    payment_id = payment_data.get("id")
    if not payment_id:
        return payment_data
    gateway_payload = AsaasGateway().get_payment(payment_id)
    return {**payment_data, **gateway_payload, "id": payment_id}


def process_webhook_event(
    event: WebhookEvent,
    *,
    payload_override: dict | None = None,
) -> WebhookEvent:
    max_retries = max(int(getattr(settings, "BILLING_WEBHOOK_MAX_RETRIES", 5)), 1)
    with transaction.atomic():
        locked = WebhookEvent.objects.select_for_update().get(pk=event.pk)
        if locked.status in {WebhookEvent.Status.PROCESSED, WebhookEvent.Status.IGNORED}:
            return locked
        locked.status = WebhookEvent.Status.PROCESSING
        locked.attempt_count += 1
        locked.save(update_fields=["status", "attempt_count", "updated_at"])

    try:
        with transaction.atomic():
            payload = payload_override or event.payload
            event_type = event.event_type
            if event_type.startswith("PAYMENT_"):
                payment_data = (
                    payload.get("payment") or {}
                    if payload_override is not None
                    else _hydrate_payment_for_worker(payload)
                )
                result = _process_payment_event(event_type, payment_data)
            elif event_type.startswith("SUBSCRIPTION_"):
                result = _process_subscription_event(
                    event_type,
                    payload.get("subscription") or {},
                )
            else:
                result = f"ignored: evento não mapeado ({event_type})"
        return _finish_event(event.pk, result, max_retries)
    except Exception as exc:
        logger.exception(
            "asaas_webhook_processing_error",
            extra={
                "event_type": event.event_type,
                "exception_type": exc.__class__.__name__,
            },
        )
        return _finish_event(
            event.pk,
            "retry: Falha interna ao processar o evento.",
            max_retries,
        )


def _process_inline_enabled() -> bool:
    configured = getattr(settings, "BILLING_WEBHOOK_PROCESS_INLINE", None)
    if configured is not None:
        return bool(configured)
    return os.getenv("BILLING_WEBHOOK_PROCESS_INLINE", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def handle_asaas_webhook(request) -> WebhookEvent:
    payload = AsaasGateway(require_api_key=False).parse_webhook(request)
    event_type = payload.get("event", "UNKNOWN")
    webhook_event = _persist_webhook_event(
        payload=payload,
        event_type=event_type,
        event_hash=_payload_hash(payload),
        event_identifier=_event_id(payload),
    )
    if _process_inline_enabled():
        return process_webhook_event(webhook_event, payload_override=payload)
    return webhook_event
