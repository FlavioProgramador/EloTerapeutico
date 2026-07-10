import uuid
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.billing.models import BillingOrder, Payment, PlanPrice, Subscription
from apps.billing.security import redact_sensitive_data
from apps.billing.services.gateways.asaas import AsaasGateway

MONEY = Decimal("0.01")


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
    estimate = (plan_price.total_amount / Decimal(count)).quantize(MONEY, rounding=ROUND_HALF_UP)
    return {
        "total_amount": plan_price.total_amount,
        "installment_count": count,
        "installment_amount_estimate": estimate,
        "discount_percentage": plan_price.discount_percentage,
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
        "total_amount": str(plan_price.total_amount),
        "currency": plan_price.currency,
        "billing_model": plan_price.billing_model,
        "billing_interval": plan_price.billing_interval,
        "discount_percentage": str(plan_price.discount_percentage),
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
        "status": payload.get("status") if payload.get("status") in Payment.Status.values else Payment.Status.PENDING,
        "due_date": _parse_date(payload.get("dueDate")),
        "original_due_date": _parse_date(payload.get("originalDueDate")),
        "paid_at": _parse_datetime(payload.get("paymentDate") or payload.get("clientPaymentDate")),
        "confirmed_at": _parse_datetime(payload.get("confirmedDate")),
        "credit_at": _parse_datetime(payload.get("creditDate")),
        "gateway_subscription_id": payload.get("subscription") or order.gateway_subscription_id,
        "gateway_installment_id": payload.get("installment") or order.gateway_installment_id,
        "installment_number": int(number) if number else (1 if count == 1 else None),
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
    payment, _ = Payment.objects.update_or_create(gateway_payment_id=payment_id, defaults=defaults)
    return payment


def sync_installment_payments(order: BillingOrder, gateway=None) -> list[Payment]:
    if not order.gateway_installment_id:
        return []
    gateway = gateway or get_gateway()
    response = gateway.list_installment_payments(order.gateway_installment_id)
    payloads = response.get("data", response if isinstance(response, list) else [])
    subscription = order.subscriptions.order_by("-created_at").first()
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
    subscription = order.subscriptions.order_by("-created_at").first()
    return [upsert_gateway_payment(order=order, payload=payload, subscription=subscription) for payload in payloads]


def create_billing_order(
    *,
    user,
    plan_price: PlanPrice,
    checkout_data: dict[str, Any],
    idempotency_key: str,
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
            subscription = existing.subscriptions.order_by("-created_at").first()
            if not subscription:
                subscription = Subscription.objects.create(
                    user=locked_user,
                    plan=existing.plan,
                    billing_order=existing,
                    status=Subscription.Status.PENDING,
                )
            return existing, subscription

        operational = Subscription.objects.select_for_update().filter(
            user=locked_user,
            status__in=[
                Subscription.Status.TRIALING,
                Subscription.Status.PENDING,
                Subscription.Status.ACTIVE,
                Subscription.Status.PAST_DUE,
                Subscription.Status.SUSPENDED,
            ],
        ).first()
        if operational:
            raise ValidationError("Você já possui uma assinatura operacional. Use a troca de plano.")

        public_id = uuid.uuid4()
        external_reference = f"elo-order-{public_id}"
        order = BillingOrder.objects.create(
            public_id=public_id,
            user=locked_user,
            plan=plan_price.plan,
            plan_price=plan_price,
            status=BillingOrder.Status.DRAFT,
            billing_model=plan_price.billing_model,
            billing_interval=plan_price.billing_interval,
            currency=plan_price.currency,
            total_amount=plan_price.total_amount,
            installment_count=preview["installment_count"],
            installment_amount_estimate=preview["installment_amount_estimate"],
            external_reference=external_reference,
            idempotency_key=idempotency_key,
            commercial_snapshot=_commercial_snapshot(plan_price),
            metadata={"checkout": _safe_snapshot(checkout_data), "provisioning_status": "PENDING"},
        )
        subscription = Subscription.objects.create(
            user=locked_user,
            plan=plan_price.plan,
            billing_order=order,
            status=Subscription.Status.PENDING,
            metadata={"activation_rule": "Acesso liberado somente após confirmação do gateway."},
        )

    gateway = get_gateway()
    customer_id = ""
    try:
        previous = BillingOrder.objects.filter(user=user).exclude(pk=order.pk).exclude(gateway_customer_id="").order_by("-created_at").first()
        customer_id = previous.gateway_customer_id if previous else ""
        if not customer_id:
            customer = gateway.create_customer(user, checkout_data)
            customer_id = customer.get("id", "")
        if not customer_id:
            raise ValidationError("Gateway não retornou o identificador do cliente.")

        gateway_data = {
            **checkout_data,
            "value": plan_price.total_amount,
            "totalValue": plan_price.total_amount,
            "installmentCount": order.installment_count,
            "externalReference": order.external_reference,
            "description": checkout_data.get("description") or f"Elo Terapêutico — {plan_price.name}",
        }
        if plan_price.billing_model == PlanPrice.BillingModel.RECURRING:
            response = gateway.create_recurring_subscription(
                user,
                plan_price,
                gateway_data,
                customer_id=customer_id,
            )
        elif plan_price.billing_model == PlanPrice.BillingModel.INSTALLMENT:
            response = gateway.create_installment_payment(
                user,
                gateway_data,
                customer_id=customer_id,
            )
        else:
            response = gateway.create_single_payment(
                user,
                gateway_data,
                customer_id=customer_id,
            )

        with transaction.atomic():
            locked_order = BillingOrder.objects.select_for_update().get(pk=order.pk)
            locked_subscription = Subscription.objects.select_for_update().get(pk=subscription.pk)
            locked_order.status = BillingOrder.Status.PENDING
            locked_order.gateway_customer_id = customer_id
            locked_order.gateway_subscription_id = response.get("id", "") if plan_price.billing_model == PlanPrice.BillingModel.RECURRING else ""
            locked_order.gateway_installment_id = response.get("installment") or ""
            locked_order.metadata = {
                **locked_order.metadata,
                "gateway_response": redact_sensitive_data(response),
                "provisioning_status": "COMPLETED",
            }
            locked_order.save()
            locked_subscription.gateway_customer_id = customer_id
            locked_subscription.gateway_subscription_id = locked_order.gateway_subscription_id
            locked_subscription.gateway_status = response.get("status", "")
            locked_subscription.save(update_fields=[
                "gateway_customer_id",
                "gateway_subscription_id",
                "gateway_status",
                "updated_at",
            ])

        if plan_price.billing_model != PlanPrice.BillingModel.RECURRING:
            upsert_gateway_payment(
                order=locked_order,
                payload=response,
                subscription=locked_subscription,
                installment_count=locked_order.installment_count,
            )
        if locked_order.gateway_installment_id:
            sync_installment_payments(locked_order, gateway=gateway)
        elif locked_order.gateway_subscription_id:
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
            Subscription.objects.filter(pk=subscription.pk, status=Subscription.Status.PENDING).update(
                status=Subscription.Status.CANCELED,
                canceled_at=timezone.now(),
            )
        raise
