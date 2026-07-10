import hashlib
import json
import logging
from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from apps.billing.models import Payment, Subscription, WebhookEvent
from apps.billing.security import redact_sensitive_data
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

PAYMENT_STATUS_TRANSITIONS = {
    Payment.Status.PENDING: {
        Payment.Status.PENDING,
        Payment.Status.CONFIRMED,
        Payment.Status.RECEIVED,
        Payment.Status.OVERDUE,
        Payment.Status.REFUNDED,
        Payment.Status.CANCELED,
        Payment.Status.FAILED,
    },
    Payment.Status.OVERDUE: {
        Payment.Status.OVERDUE,
        Payment.Status.CONFIRMED,
        Payment.Status.RECEIVED,
        Payment.Status.REFUNDED,
        Payment.Status.CANCELED,
    },
    Payment.Status.CONFIRMED: {
        Payment.Status.CONFIRMED,
        Payment.Status.RECEIVED,
        Payment.Status.REFUNDED,
    },
    Payment.Status.RECEIVED: {
        Payment.Status.RECEIVED,
        Payment.Status.REFUNDED,
    },
    Payment.Status.REFUNDED: {Payment.Status.REFUNDED},
    Payment.Status.CANCELED: {Payment.Status.CANCELED},
    Payment.Status.FAILED: {
        Payment.Status.FAILED,
        Payment.Status.PENDING,
        Payment.Status.CONFIRMED,
        Payment.Status.RECEIVED,
    },
}


def _payload_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _event_id(payload: dict) -> str | None:
    explicit_id = payload.get("id") or payload.get("eventId")
    if explicit_id:
        return explicit_id
    event_type = payload.get("event", "UNKNOWN")
    payment = payload.get("payment") or {}
    subscription = payload.get("subscription") or {}
    related_id = payment.get("id") or subscription.get("id")
    return f"{event_type}:{related_id}" if related_id else None


def _parse_paid_at(payment_data: dict):
    paid_at = payment_data.get("paymentDate") or payment_data.get("confirmedDate") or payment_data.get("clientPaymentDate")
    if not paid_at:
        return None
    try:
        parsed = datetime.fromisoformat(paid_at)
    except ValueError:
        return timezone.now()
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _parse_due_date(payment_data: dict):
    due_date = payment_data.get("dueDate")
    if not due_date:
        return None
    try:
        return datetime.fromisoformat(due_date).date()
    except ValueError:
        return None


def _can_transition_payment(current_status: str, next_status: str) -> bool:
    return next_status in PAYMENT_STATUS_TRANSITIONS.get(current_status, {current_status})


def _upsert_payment(subscription: Subscription, payment_data: dict, event_type: str) -> Payment:
    gateway_payment_id = payment_data.get("id")
    if not gateway_payment_id:
        raise ValidationError("Evento de pagamento sem identificador do gateway.")

    next_status = PAYMENT_STATUS_BY_EVENT.get(event_type, Payment.Status.PENDING)
    defaults = {
        "subscription": subscription,
        "user": subscription.user,
        "amount": Decimal(str(payment_data.get("value") or subscription.plan.price)),
        "currency": subscription.plan.currency,
        "status": next_status,
        "due_date": _parse_due_date(payment_data),
        "paid_at": _parse_paid_at(payment_data) if next_status in {Payment.Status.CONFIRMED, Payment.Status.RECEIVED} else None,
        "gateway_subscription_id": payment_data.get("subscription") or subscription.gateway_subscription_id,
        "invoice_url": payment_data.get("invoiceUrl") or "",
        "bank_slip_url": payment_data.get("bankSlipUrl") or "",
        "pix_qr_code": payment_data.get("pixQrCode") or "",
        "pix_copy_paste": payment_data.get("pixCopyPaste") or "",
        "raw_payload": redact_sensitive_data(payment_data),
    }

    payment, created = Payment.objects.select_for_update().get_or_create(
        gateway_payment_id=gateway_payment_id,
        defaults=defaults,
    )
    if created:
        return payment

    update_fields = []
    for field, value in defaults.items():
        if field == "status":
            continue
        setattr(payment, field, value)
        update_fields.append(field)

    if _can_transition_payment(payment.status, next_status):
        payment.status = next_status
        update_fields.append("status")

    payment.save(update_fields=[*update_fields, "updated_at"])
    return payment


def _process_payment_event(event_type: str, payment_data: dict) -> str:
    gateway_subscription_id = payment_data.get("subscription")
    if not gateway_subscription_id:
        return "Evento de pagamento sem subscription no payload."

    subscription = (
        Subscription.objects.select_for_update()
        .select_related("plan", "user")
        .filter(gateway_subscription_id=gateway_subscription_id)
        .first()
    )
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

    subscription = (
        Subscription.objects.select_for_update()
        .filter(gateway_subscription_id=gateway_subscription_id)
        .first()
    )
    if not subscription:
        return f"Assinatura local não encontrada para {gateway_subscription_id}."

    subscription.gateway_status = subscription_data.get("status", subscription.gateway_status)
    subscription.metadata = {
        **(subscription.metadata or {}),
        "last_subscription_webhook": redact_sensitive_data(subscription_data),
    }
    update_fields = ["gateway_status", "metadata", "updated_at"]
    if event_type == "SUBSCRIPTION_DELETED":
        subscription.status = Subscription.Status.CANCELED
        subscription.canceled_at = timezone.now()
        update_fields += ["status", "canceled_at"]
    subscription.save(update_fields=update_fields)
    return "processed"


def _persist_webhook_event(*, payload: dict, event_type: str, event_hash: str, event_identifier: str | None) -> WebhookEvent:
    defaults = {
        "gateway_name": "ASAAS",
        "event_type": event_type,
        "payload": redact_sensitive_data(payload),
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


def handle_asaas_webhook(request) -> WebhookEvent:
    """Persiste o evento e processa seus efeitos em uma transação separada e curta."""
    payload = AsaasGateway(require_api_key=False).parse_webhook(request)
    event_type = payload.get("event", "UNKNOWN")
    event_hash = _payload_hash(payload)
    event_identifier = _event_id(payload)
    webhook_event = _persist_webhook_event(
        payload=payload,
        event_type=event_type,
        event_hash=event_hash,
        event_identifier=event_identifier,
    )

    if webhook_event.processed:
        return webhook_event

    try:
        with transaction.atomic():
            locked_event = WebhookEvent.objects.select_for_update().get(pk=webhook_event.pk)
            if locked_event.processed:
                return locked_event

            if event_type.startswith("PAYMENT_"):
                result = _process_payment_event(event_type, payload.get("payment") or {})
            elif event_type.startswith("SUBSCRIPTION_"):
                result = _process_subscription_event(event_type, payload.get("subscription") or {})
            else:
                result = f"Evento ignorado: {event_type}."

            locked_event.error_message = "" if result == "processed" else result
            locked_event.processed = True
            locked_event.processed_at = timezone.now()
            locked_event.save(update_fields=["processed", "processed_at", "error_message"])
            return locked_event
    except Exception as exc:
        logger.error(
            "asaas_webhook_processing_error",
            extra={
                "event_type": event_type,
                "exception_type": exc.__class__.__name__,
            },
        )
        with transaction.atomic():
            locked_event = WebhookEvent.objects.select_for_update().get(pk=webhook_event.pk)
            if not locked_event.processed:
                locked_event.error_message = "Falha interna ao processar o evento."
                locked_event.processed_at = None
                locked_event.save(update_fields=["processed_at", "error_message"])
            return locked_event
