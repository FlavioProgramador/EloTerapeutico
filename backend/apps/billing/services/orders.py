import uuid
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.billing.infrastructure.payments.asaas.client import AsaasGateway
from apps.billing.models import BillingOrder, Payment, PlanPrice, Subscription
from apps.billing.security import redact_sensitive_data

MONEY = Decimal("0.01")
OPERATIONAL_SUBSCRIPTION_STATUSES = [
    Subscription.Status.TRIALING,
    Subscription.Status.PENDING,
    Subscription.Status.ACTIVE,
    Subscription.Status.PAST_DUE,
    Subscription.Status.SUSPENDED,
]
PAYMENT_STATUS_TRANSITIONS = {
    Payment.Status.PENDING: set(Payment.Status.values),
    Payment.Status.AUTHORIZED: {
        Payment.Status.AUTHORIZED,
        Payment.Status.CONFIRMED,
        Payment.Status.RECEIVED,
        Payment.Status.OVERDUE,
        Payment.Status.CANCELED,
        Payment.Status.FAILED,
        Payment.Status.REFUNDED,
        Payment.Status.PARTIALLY_REFUNDED,
        Payment.Status.REFUND_IN_PROGRESS,
        Payment.Status.CHARGEBACK,
        Payment.Status.CHARGEBACK_DISPUTE,
        Payment.Status.AWAITING_RISK_ANALYSIS,
    },
    Payment.Status.OVERDUE: {
        Payment.Status.OVERDUE,
        Payment.Status.CONFIRMED,
        Payment.Status.RECEIVED,
        Payment.Status.CANCELED,
        Payment.Status.REFUNDED,
        Payment.Status.PARTIALLY_REFUNDED,
        Payment.Status.REFUND_IN_PROGRESS,
        Payment.Status.CHARGEBACK,
        Payment.Status.CHARGEBACK_DISPUTE,
    },
    Payment.Status.CONFIRMED: {
        Payment.Status.CONFIRMED,
        Payment.Status.RECEIVED,
        Payment.Status.REFUNDED,
        Payment.Status.PARTIALLY_REFUNDED,
        Payment.Status.REFUND_IN_PROGRESS,
        Payment.Status.CHARGEBACK,
        Payment.Status.CHARGEBACK_DISPUTE,
    },
    Payment.Status.RECEIVED: {
        Payment.Status.RECEIVED,
        Payment.Status.REFUNDED,
        Payment.Status.PARTIALLY_REFUNDED,
        Payment.Status.REFUND_IN_PROGRESS,
        Payment.Status.CHARGEBACK,
        Payment.Status.CHARGEBACK_DISPUTE,
    },
    Payment.Status.FAILED: {
        Payment.Status.FAILED,
        Payment.Status.PENDING,
        Payment.Status.AUTHORIZED,
        Payment.Status.CONFIRMED,
        Payment.Status.RECEIVED,
    },
    Payment.Status.CANCELED: {Payment.Status.CANCELED, Payment.Status.RESTORED},
    Payment.Status.REFUNDED: {Payment.Status.REFUNDED},
    Payment.Status.PARTIALLY_REFUNDED: {
        Payment.Status.PARTIALLY_REFUNDED,
        Payment.Status.REFUNDED,
    },
    Payment.Status.REFUND_IN_PROGRESS: {
        Payment.Status.REFUND_IN_PROGRESS,
        Payment.Status.PARTIALLY_REFUNDED,
        Payment.Status.REFUNDED,
    },
    Payment.Status.CHARGEBACK: {
        Payment.Status.CHARGEBACK,
        Payment.Status.CHARGEBACK_DISPUTE,
        Payment.Status.RESTORED,
    },
    Payment.Status.CHARGEBACK_DISPUTE: {
        Payment.Status.CHARGEBACK_DISPUTE,
        Payment.Status.CHARGEBACK,
        Payment.Status.RESTORED,
    },
    Payment.Status.RESTORED: {
        Payment.Status.RESTORED,
        Payment.Status.CONFIRMED,
        Payment.Status.RECEIVED,
    },
    Payment.Status.AWAITING_RISK_ANALYSIS: {
        Payment.Status.AWAITING_RISK_ANALYSIS,
        Payment.Status.CONFIRMED,
        Payment.Status.FAILED,
    },
}


def get_gateway():
    return AsaasGateway()


def _decimal(value, default="0") -> Decimal:
    return Decimal(str(value if value is not None else default)).quantize(MONEY, rounding=ROUND_HALF_UP)


def _safe_snapshot(data: dict[str, Any] | None) -> dict[str, Any]:
    blocked = {"cpfCnpj", "creditCardToken", "creditCard", "creditCardHolderInfo", "remoteIp"}
    snapshot = {}
    for key, value in (data or {}).items():
        if key in blocked or key in {"plan", "plan_price"}:
            continue
        if isinstance(value, (date, datetime)):
            snapshot[key] = value.isoformat()
        elif isinstance(value, Decimal):
            snapshot[key] = str(value)
        else:
            snapshot[key] = value
    return snapshot


def validate_installments(plan_price: PlanPrice, installment_count: int) -> int:
    count = int(installment_count or 1)
    if plan_price.billing_model == PlanPrice.BillingModel.INSTALLMENT:
        if not plan_price.installments_enabled:
            raise ValidationError("Este preço não permite parcelamento.")
        if count < plan_price.min_installments or count > plan_price.max_installments:
            raise ValidationError(
                f"Selecione entre {plan_price.min_installments} e {plan_price.max_installments} parcelas."
            )
    elif count != 1:
        raise ValidationError("Esta modalidade deve ser paga em uma única cobrança.")
    return count


def preview_order(plan_price: PlanPrice, installment_count: int = 1) -> dict[str, Any]:
    if not plan_price.is_available():
        raise ValidationError("Esta opção de contratação não está disponível.")
    count = validate_installments(plan_price, installment_count)
    total_amount = _decimal(plan_price.total_amount)
    estimate = (total_amount / Decimal(count)).quantize(MONEY, rounding=ROUND_HALF_UP)
    return {
        "total_amount": total_amount,
        "installment_count": count,
        "installment_amount_estimate": estimate,
        "discount_percentage": _decimal(plan_price.discount_percentage),
        "billing_model": plan_price.billing_model,
        "billing_interval": plan_price.billing_interval,
    }


def _commercial_snapshot(plan_price: PlanPrice) -> dict[str, Any]:
    plan = plan_price.plan
    return {
        "plan_id": plan.pk,
        "plan_name": plan.name,
        "plan_slug": plan.slug,
        "price_id": plan_price.pk,
        "price_name": plan_price.name,
        "price_slug": plan_price.slug,
        "total_amount": str(_decimal(plan_price.total_amount)),
        "currency": plan_price.currency,
        "billing_model": plan_price.billing_model,
        "billing_interval": plan_price.billing_interval,
        "discount_percentage": str(_decimal(plan_price.discount_percentage)),
        "features": {
            "agenda": plan.has_agenda,
            "patients": plan.has_patients,
            "clinical_records": plan.has_clinical_records,
            "financial": plan.has_financial,
            "documents": plan.has_documents,
            "forms": plan.has_forms,
            "reports": plan.has_reports,
            "ai": plan.has_ai,
        },
    }


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None


def _parse_datetime(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return timezone.make_aware(parsed, timezone.get_current_timezone()) if timezone.is_naive(parsed) else parsed


def _can_transition_payment(current_status: str, next_status: str) -> bool:
    return next_status in PAYMENT_STATUS_TRANSITIONS.get(current_status, {current_status})


def upsert_gateway_payment(
    *,
    order: BillingOrder,
    payload: dict[str, Any],
    subscription: Subscription | None = None,
    installment_count: int | None = None,
) -> Payment:
    payment_id = payload.get("id")
    if not payment_id:
        raise ValidationError("Gateway não retornou o identificador da cobrança.")
    count = int(installment_count or order.installment_count or 1)
    number = payload.get("installmentNumber")
    installment_number = int(number) if number else (1 if count == 1 else None)
    next_status = payload.get("status") if payload.get("status") in Payment.Status.values else Payment.Status.PENDING
    defaults = {
        "billing_order": order,
        "subscription": subscription,
        "user": order.user,
        "amount": _decimal(payload.get("value") or order.installment_amount_estimate or order.total_amount),
        "net_amount": _decimal(payload.get("netValue")) if payload.get("netValue") is not None else None,
        "interest_amount": _decimal(payload.get("interestValue")),
        "fine_amount": _decimal((payload.get("fine") or {}).get("value")),
        "discount_amount": _decimal((payload.get("discount") or {}).get("value")),
        "currency": order.currency,
        "billing_type": payload.get("billingType") or Payment.BillingType.UNDEFINED,
        "due_date": _parse_date(payload.get("dueDate")),
        "original_due_date": _parse_date(payload.get("originalDueDate")),
        "paid_at": _parse_datetime(payload.get("paymentDate") or payload.get("clientPaymentDate")),
        "confirmed_at": _parse_datetime(payload.get("confirmedDate")),
        "credit_at": _parse_datetime(payload.get("creditDate")),
        "gateway_subscription_id": payload.get("subscription") or order.gateway_subscription_id,
        "gateway_installment_id": payload.get("installment") or order.gateway_installment_id,
        "installment_number": installment_number,
        "installment_count": count,
        "invoice_number": payload.get("invoiceNumber") or "",
        "invoice_url": payload.get("invoiceUrl") or "",
        "bank_slip_url": payload.get("bankSlipUrl") or "",
        "transaction_receipt_url": payload.get("transactionReceiptUrl") or "",
        "pix_qr_code": payload.get("pixQrCode") or "",
        "pix_copy_paste": payload.get("pixCopyPaste") or "",
        "external_reference": payload.get("externalReference") or order.external_reference,
        "raw_payload": redact_sensitive_data(payload),
    }

    existing = Payment.objects.filter(gateway_payment_id=payment_id).first()
    if not existing and installment_number is not None:
        existing = Payment.objects.filter(
            billing_order=order,
            installment_number=installment_number,
        ).first()
    if existing:
        for field, value in defaults.items():
            current = getattr(existing, field, None)
            if value not in (None, "") or current in (None, ""):
                setattr(existing, field, value)
        if _can_transition_payment(existing.status, next_status):
            existing.status = next_status
        existing.gateway_payment_id = payment_id
        existing.save()
        return existing

    try:
        return Payment.objects.create(gateway_payment_id=payment_id, status=next_status, **defaults)
    except IntegrityError:
        payment = Payment.objects.select_for_update().get(
            billing_order=order,
            installment_number=installment_number,
        )
        for field, value in defaults.items():
            current = getattr(payment, field, None)
            if value not in (None, "") or current in (None, ""):
                setattr(payment, field, value)
        if _can_transition_payment(payment.status, next_status):
            payment.status = next_status
        payment.gateway_payment_id = payment_id
        payment.save()
        return payment


def sync_installment_payments(order: BillingOrder, gateway=None) -> list[Payment]:
    if not order.gateway_installment_id:
        return []
    gateway = gateway or get_gateway()
    response = gateway.list_installment_payments(order.gateway_installment_id)
    payloads = response.get("data", response if isinstance(response, list) else [])
    subscription = _subscription_for_order(order)
    return [
        upsert_gateway_payment(
            order=order,
            payload=payload,
            subscription=subscription,
            installment_count=order.installment_count,
        )
        for payload in payloads
    ]


def sync_subscription_payments(order: BillingOrder, gateway=None) -> list[Payment]:
    if not order.gateway_subscription_id:
        return []
    gateway = gateway or get_gateway()
    response = gateway.list_subscription_payments(order.gateway_subscription_id)
    payloads = response.get("data", response if isinstance(response, list) else [])
    subscription = _subscription_for_order(order)
    return [upsert_gateway_payment(order=order, payload=payload, subscription=subscription) for payload in payloads]


def _subscription_for_order(order: BillingOrder) -> Subscription | None:
    subscription = order.subscriptions.order_by("-created_at").first()
    if subscription:
        return subscription
    source_id = (order.metadata or {}).get("plan_change_from_subscription_id")
    return Subscription.objects.filter(pk=source_id).first() if source_id else None


def _existing_order_subscription(order: BillingOrder, user) -> Subscription:
    subscription = _subscription_for_order(order)
    if subscription:
        return subscription
    operational = Subscription.objects.filter(user=user, status__in=OPERATIONAL_SUBSCRIPTION_STATUSES).first()
    if operational:
        return operational
    return Subscription.objects.create(
        user=user,
        plan=order.plan,
        billing_order=order,
        status=Subscription.Status.PENDING,
    )


def create_billing_order(
    *,
    user,
    plan_price: PlanPrice,
    checkout_data: dict[str, Any],
    idempotency_key: str,
    gateway=None,
) -> tuple[BillingOrder, Subscription]:
    if not idempotency_key or len(idempotency_key) < 8:
        raise ValidationError("Informe uma chave de idempotência válida.")
    preview = preview_order(plan_price, checkout_data.get("installmentCount", 1))
    user_model = get_user_model()

    with transaction.atomic():
        locked_user = user_model.objects.select_for_update().get(pk=user.pk)
        existing = BillingOrder.objects.select_related("plan", "plan_price").filter(
            user=locked_user,
            idempotency_key=idempotency_key,
        ).first()
        if existing:
            return existing, _existing_order_subscription(existing, locked_user)

        operational = (
            Subscription.objects.select_for_update()
            .select_related("billing_order", "billing_order__plan_price")
            .filter(user=locked_user, status__in=OPERATIONAL_SUBSCRIPTION_STATUSES)
            .first()
        )
        if operational and operational.status in {Subscription.Status.PENDING, Subscription.Status.TRIALING}:
            raise ValidationError("Já existe uma contratação pendente ou período de teste em andamento.")
        if operational and operational.billing_order_id and operational.billing_order.plan_price_id == plan_price.pk:
            raise ValidationError("Você já utiliza esta modalidade de plano.")

        is_plan_change = operational is not None
        public_id = uuid.uuid4()
        external_reference = f"elo-order-{public_id}"
        metadata = {
            "checkout": _safe_snapshot(checkout_data),
            "provisioning_status": "PENDING",
            "is_plan_change": is_plan_change,
        }
        if operational:
            metadata.update(
                {
                    "plan_change_from_subscription_id": operational.pk,
                    "previous_plan_id": operational.plan_id,
                    "previous_billing_order_id": operational.billing_order_id,
                    "previous_gateway_subscription_id": operational.gateway_subscription_id,
                }
            )

        order = BillingOrder.objects.create(
            public_id=public_id,
            user=locked_user,
            plan=plan_price.plan,
            plan_price=plan_price,
            status=BillingOrder.Status.DRAFT,
            billing_model=plan_price.billing_model,
            billing_interval=plan_price.billing_interval,
            currency=plan_price.currency,
            total_amount=preview["total_amount"],
            installment_count=preview["installment_count"],
            installment_amount_estimate=preview["installment_amount_estimate"],
            external_reference=external_reference,
            idempotency_key=idempotency_key,
            commercial_snapshot=_commercial_snapshot(plan_price),
            metadata=metadata,
        )
        if operational:
            subscription = operational
        else:
            subscription = Subscription.objects.create(
                user=locked_user,
                plan=plan_price.plan,
                billing_order=order,
                status=Subscription.Status.PENDING,
                metadata={
                    "activation_rule": "Acesso liberado somente após confirmação do gateway.",
                    "provisioning_status": "PENDING",
                },
            )

    gateway = gateway or get_gateway()
    customer_id = ""
    created_new_subscription = not is_plan_change
    try:
        previous = (
            BillingOrder.objects.filter(user=user)
            .exclude(pk=order.pk)
            .exclude(gateway_customer_id="")
            .order_by("-created_at")
            .first()
        )
        customer_id = previous.gateway_customer_id if previous else subscription.gateway_customer_id
        if not customer_id:
            customer = gateway.create_customer(user, checkout_data)
            customer_id = customer.get("id", "")
        if not customer_id:
            raise ValidationError("Gateway não retornou o identificador do cliente.")

        gateway_data = {
            **checkout_data,
            "value": preview["total_amount"],
            "totalValue": preview["total_amount"],
            "installmentCount": order.installment_count,
            "externalReference": order.external_reference,
            "description": checkout_data.get("description") or f"Elo Terapêutico — {plan_price.name}",
        }
        if plan_price.billing_model == PlanPrice.BillingModel.RECURRING:
            if hasattr(gateway, "create_recurring_subscription"):
                response = gateway.create_recurring_subscription(
                    user,
                    plan_price,
                    gateway_data,
                    customer_id=customer_id,
                )
            else:
                response = gateway.create_subscription(
                    user,
                    plan_price.plan,
                    gateway_data,
                    customer_id=customer_id,
                )
        elif plan_price.billing_model == PlanPrice.BillingModel.INSTALLMENT:
            response = gateway.create_installment_payment(user, gateway_data, customer_id=customer_id)
        else:
            response = gateway.create_single_payment(user, gateway_data, customer_id=customer_id)

        with transaction.atomic():
            locked_order = BillingOrder.objects.select_for_update().get(pk=order.pk)
            locked_subscription = Subscription.objects.select_for_update().get(pk=subscription.pk)
            locked_order.status = BillingOrder.Status.PENDING
            locked_order.gateway_customer_id = customer_id
            locked_order.gateway_subscription_id = (
                response.get("id", "") if plan_price.billing_model == PlanPrice.BillingModel.RECURRING else ""
            )
            locked_order.gateway_installment_id = response.get("installment") or ""
            locked_order.metadata = {
                **locked_order.metadata,
                "gateway_response": redact_sensitive_data(response),
                "provisioning_status": "COMPLETED",
            }
            locked_order.save()
            if created_new_subscription:
                locked_subscription.gateway_customer_id = customer_id
                locked_subscription.gateway_subscription_id = locked_order.gateway_subscription_id
                locked_subscription.gateway_status = response.get("status", "")
                locked_subscription.metadata = {
                    **(locked_subscription.metadata or {}),
                    "provisioning_status": "COMPLETED",
                }
                locked_subscription.save(
                    update_fields=[
                        "gateway_customer_id",
                        "gateway_subscription_id",
                        "gateway_status",
                        "metadata",
                        "updated_at",
                    ]
                )

        if plan_price.billing_model != PlanPrice.BillingModel.RECURRING:
            upsert_gateway_payment(
                order=locked_order,
                payload=response,
                subscription=locked_subscription,
                installment_count=locked_order.installment_count,
            )
        if locked_order.gateway_installment_id and hasattr(gateway, "list_installment_payments"):
            sync_installment_payments(locked_order, gateway=gateway)
        elif locked_order.gateway_subscription_id and hasattr(gateway, "list_subscription_payments"):
            sync_subscription_payments(locked_order, gateway=gateway)
        return locked_order, locked_subscription
    except Exception as exc:
        with transaction.atomic():
            failed_order = BillingOrder.objects.select_for_update().get(pk=order.pk)
            failed_order.status = BillingOrder.Status.FAILED
            failed_order.failed_at = timezone.now()
            failed_order.metadata = {
                **failed_order.metadata,
                "provisioning_status": "FAILED",
                "error_code": exc.__class__.__name__,
            }
            failed_order.save(update_fields=["status", "failed_at", "metadata", "updated_at"])
            if created_new_subscription:
                failed_subscription = Subscription.objects.select_for_update().get(pk=subscription.pk)
                if failed_subscription.status == Subscription.Status.PENDING:
                    failed_subscription.status = Subscription.Status.CANCELED
                    failed_subscription.canceled_at = timezone.now()
                    failed_subscription.metadata = {
                        **(failed_subscription.metadata or {}),
                        "provisioning_status": "FAILED",
                        "provisioning_error_code": exc.__class__.__name__,
                    }
                    failed_subscription.save(
                        update_fields=["status", "canceled_at", "metadata", "updated_at"]
                    )
        raise
