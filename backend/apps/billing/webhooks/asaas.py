import hashlib
import json
import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.billing.models import Payment, Subscription, WebhookEvent
from apps.billing.services.gateways.asaas import AsaasGateway
from apps.billing.services.subscriptions import activate_subscription_from_payment, mark_subscription_past_due

logger = logging.getLogger(__name__)

PAYMENT_STATUS_BY_EVENT = {
    "PAYMENT_CREATED": Payment.Status.PENDING,
    "PAYMENT_CONFIRMED": Payment.Status.CONFIRMED,
    "PAYMENT_RECEIVED": Payment.Status.RECEIVED,
    "PAYMENT_OVERDUE": Payment.Status.OVERDUE,
    "PAYMENT_DELETED": Payment.Status.CANCELED,
    "PAYMENT_REFUNDED": Payment.Status.REFUNDED,
}


def _payload_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _event_id(payload: dict) -> str | None:
    payment = payload.get("payment") or {}
    subscription = payload.get("subscription") or {}
    return payload.get("id") or payload.get("eventId") or payment.get("id") or subscription.get("id")


def _parse_paid_at(payment_data: dict):
    paid_at = payment_data.get("paymentDate") or payment_data.get("confirmedDate") or payment_data.get("clientPaymentDate")
    if not paid_at:
        return None
    try:
        return timezone.datetime.fromisoformat(paid_at).replace(tzinfo=timezone.get_current_timezone())
    except ValueError:
        return timezone.now()


def _parse_due_date(payment_data: dict):
    due_date = payment_data.get("dueDate")
    if not due_date:
        return None
    try:
        return timezone.datetime.fromisoformat(due_date).date()
    except ValueError:
        return None


def _upsert_payment(subscription: Subscription, payment_data: dict, event_type: str) -> Payment:
    gateway_payment_id = payment_data.get("id")
    status = PAYMENT_STATUS_BY_EVENT.get(event_type, Payment.Status.PENDING)
    defaults = {
        "subscription": subscription,
        "user": subscription.user,
        "amount": Decimal(str(payment_data.get("value") or subscription.plan.price)),
        "currency": subscription.plan.currency,
        "status": status,
        "due_date": _parse_due_date(payment_data),
        "paid_at": _parse_paid_at(payment_data) if status in {Payment.Status.CONFIRMED, Payment.Status.RECEIVED} else None,
        "gateway_subscription_id": payment_data.get("subscription") or subscription.gateway_subscription_id,
        "invoice_url": payment_data.get("invoiceUrl") or "",
        "bank_slip_url": payment_data.get("bankSlipUrl") or "",
        "pix_qr_code": payment_data.get("pixQrCode") or "",
        "pix_copy_paste": payment_data.get("pixCopyPaste") or "",
        "raw_payload": payment_data,
    }
    if gateway_payment_id:
        payment, _ = Payment.objects.update_or_create(gateway_payment_id=gateway_payment_id, defaults=defaults)
        return payment
    return Payment.objects.create(gateway_payment_id=None, **defaults)


def _process_payment_event(event_type: str, payment_data: dict) -> str:
    gateway_subscription_id = payment_data.get("subscription")
    if not gateway_subscription_id:
        return "Evento de pagamento sem subscription no payload."
    subscription = Subscription.objects.select_related("plan", "user").filter(
        gateway_subscription_id=gateway_subscription_id,
    ).first()
    if not subscription:
        return f"Assinatura local não encontrada para {gateway_subscription_id}."
    payment = _upsert_payment(subscription, payment_data, event_type)
    if event_type in {"PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"}:
        activate_subscription_from_payment(subscription, payment)
    elif event_type == "PAYMENT_OVERDUE":
        mark_subscription_past_due(subscription)
    return "processed"


def _process_subscription_event(event_type: str, subscription_data: dict) -> str:
    gateway_subscription_id = subscription_data.get("id")
    if not gateway_subscription_id:
        return "Evento de assinatura sem id no payload."
    subscription = Subscription.objects.filter(gateway_subscription_id=gateway_subscription_id).first()
    if not subscription:
        return f"Assinatura local não encontrada para {gateway_subscription_id}."
    subscription.gateway_status = subscription_data.get("status", subscription.gateway_status)
    subscription.metadata = {**subscription.metadata, "last_subscription_webhook": subscription_data}
    update_fields = ["gateway_status", "metadata", "updated_at"]
    if event_type == "SUBSCRIPTION_DELETED":
        subscription.status = Subscription.Status.CANCELED
        subscription.canceled_at = timezone.now()
        update_fields += ["status", "canceled_at"]
    subscription.save(update_fields=update_fields)
    return "processed"


@transaction.atomic
def handle_asaas_webhook(request) -> WebhookEvent:
    payload = AsaasGateway().parse_webhook(request)
    event_type = payload.get("event", "UNKNOWN")
    event_hash = _payload_hash(payload)
    webhook_event, created = WebhookEvent.objects.get_or_create(
        payload_hash=event_hash,
        defaults={
            "gateway_name": "ASAAS",
            "event_id": _event_id(payload),
            "event_type": event_type,
            "payload": payload,
        },
    )
    if not created and webhook_event.processed:
        return webhook_event

    try:
        if event_type.startswith("PAYMENT_"):
            result = _process_payment_event(event_type, payload.get("payment") or {})
        elif event_type.startswith("SUBSCRIPTION_"):
            result = _process_subscription_event(event_type, payload.get("subscription") or {})
        else:
            result = f"Evento ignorado: {event_type}."
        webhook_event.error_message = "" if result == "processed" else result
        webhook_event.processed = True
        webhook_event.processed_at = timezone.now()
        webhook_event.save(update_fields=["processed", "processed_at", "error_message"])
    except Exception as exc:
        logger.exception("asaas_webhook_processing_error", extra={"event_type": event_type})
        webhook_event.error_message = str(exc)
        webhook_event.processed = False
        webhook_event.save(update_fields=["processed", "error_message"])
    return webhook_event
