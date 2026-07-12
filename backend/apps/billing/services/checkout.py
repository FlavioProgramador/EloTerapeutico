import uuid
from datetime import timedelta
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.billing.models import BillingOrder, PlanPrice, Subscription
from apps.billing.security import redact_sensitive_data
from apps.billing.services.gateways.asaas import AsaasGateway
from apps.billing.services.orders import (
    OPERATIONAL_SUBSCRIPTION_STATUSES,
    _commercial_snapshot,
    _existing_order_subscription,
    _safe_snapshot,
    preview_order,
    sync_installment_payments,
    sync_subscription_payments,
    upsert_gateway_payment,
)


class CheckoutBusinessError(Exception):
    code = "CHECKOUT_ERROR"
    http_status = 400
    public_message = "Não foi possível iniciar a contratação."

    def __init__(self, message: str | None = None, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message or self.public_message)
        self.details = details or {}


class CheckoutAlreadyPendingError(CheckoutBusinessError):
    code = "CHECKOUT_ALREADY_PENDING"
    http_status = 409
    public_message = "Já existe uma contratação aguardando pagamento."


class CheckoutSamePlanError(CheckoutBusinessError):
    code = "CHECKOUT_SAME_PLAN"
    http_status = 400
    public_message = "Você já utiliza esta modalidade de plano."


@dataclass(frozen=True)
class CheckoutResult:
    order: BillingOrder
    subscription: Subscription
    created: bool


def _storage_idempotency_key(user_id: int, key: str) -> str:
    normalized = str(key or "").strip()
    if len(normalized) < 8:
        raise CheckoutBusinessError(
            "Informe uma chave de idempotência válida.",
            details={"idempotency_key": ["Use ao menos 8 caracteres."]},
        )
    namespaced = f"user:{user_id}:{normalized}"
    if len(namespaced) > 160:
        raise CheckoutBusinessError(
            "A chave de idempotência é muito longa.",
            details={"idempotency_key": ["Use no máximo 140 caracteres."]},
        )
    return namespaced


def _pending_order_for_user(user, plan_price: PlanPrice) -> BillingOrder | None:
    expiration_minutes = max(int(getattr(settings, "BILLING_CHECKOUT_EXPIRATION_MINUTES", 30)), 1)
    cutoff = timezone.now() - timedelta(minutes=expiration_minutes)
    candidates = (
        BillingOrder.objects.select_for_update()
        .filter(
            user=user,
            plan_price=plan_price,
            status__in=[BillingOrder.Status.DRAFT, BillingOrder.Status.PENDING],
        )
        .order_by("-created_at")
    )
    for order in candidates:
        if order.status == BillingOrder.Status.DRAFT and order.created_at < cutoff:
            order.status = BillingOrder.Status.EXPIRED
            order.save(update_fields=["status", "updated_at"])
            continue
        return order
    return None


def _gateway_customer_id(user, subscription: Subscription) -> str:
    previous = (
        BillingOrder.objects.filter(user=user)
        .exclude(gateway_customer_id="")
        .order_by("-created_at")
        .first()
    )
    return previous.gateway_customer_id if previous else subscription.gateway_customer_id


def create_checkout_order(
    *,
    user,
    plan_price: PlanPrice,
    checkout_data: dict[str, Any],
    idempotency_key: str,
    gateway=None,
) -> CheckoutResult:
    """Cria a intenção de pagamento sem remover acesso vigente antes do webhook."""

    preview = preview_order(plan_price, checkout_data.get("installmentCount", 1))
    user_model = get_user_model()
    storage_key = _storage_idempotency_key(user.pk, idempotency_key)

    with transaction.atomic():
        locked_user = user_model.objects.select_for_update().get(pk=user.pk)
        existing = (
            BillingOrder.objects.select_related("plan", "plan_price")
            .filter(user=locked_user, idempotency_key=storage_key)
            .first()
        )
        if existing:
            return CheckoutResult(
                order=existing,
                subscription=_existing_order_subscription(existing, locked_user),
                created=False,
            )

        pending_order = _pending_order_for_user(locked_user, plan_price)
        if pending_order:
            return CheckoutResult(
                order=pending_order,
                subscription=_existing_order_subscription(pending_order, locked_user),
                created=False,
            )

        operational = (
            Subscription.objects.select_for_update()
            .select_related("billing_order", "billing_order__plan_price", "plan")
            .filter(user=locked_user, status__in=OPERATIONAL_SUBSCRIPTION_STATUSES)
            .first()
        )
        if operational and operational.status == Subscription.Status.PENDING:
            details: dict[str, Any] = {}
            if operational.billing_order_id:
                details["order_public_id"] = str(operational.billing_order.public_id)
            raise CheckoutAlreadyPendingError(details=details)
        if (
            operational
            and operational.status != Subscription.Status.TRIALING
            and operational.billing_order_id
            and operational.billing_order.plan_price_id == plan_price.pk
        ):
            raise CheckoutSamePlanError()

        public_id = uuid.uuid4()
        is_trial_conversion = bool(
            operational and operational.status == Subscription.Status.TRIALING
        )
        is_plan_change = bool(operational and operational.plan_id != plan_price.plan_id)
        metadata: dict[str, Any] = {
            "checkout": _safe_snapshot(checkout_data),
            "provisioning_status": "PENDING",
            "is_plan_change": is_plan_change,
            "conversion_from_trial": is_trial_conversion,
            "client_idempotency_key": str(idempotency_key),
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
            external_reference=f"elo-order-{public_id}",
            idempotency_key=storage_key,
            commercial_snapshot=_commercial_snapshot(plan_price),
            metadata=metadata,
        )
        created_new_subscription = operational is None
        if operational:
            subscription = operational
            subscription.metadata = {
                **(subscription.metadata or {}),
                "pending_checkout": {
                    "order_public_id": str(order.public_id),
                    "target_plan_id": plan_price.plan_id,
                    "status": "AWAITING_PAYMENT",
                    "requested_at": timezone.now().isoformat(),
                },
            }
            subscription.save(update_fields=["metadata", "updated_at"])
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

    gateway = gateway or AsaasGateway()
    try:
        customer_id = _gateway_customer_id(user, subscription)
        if not customer_id:
            customer = gateway.create_customer(user, checkout_data)
            customer_id = str(customer.get("id") or "")
        if not customer_id:
            raise CheckoutBusinessError("Gateway não retornou o identificador do cliente.")

        BillingOrder.objects.filter(pk=order.pk).update(gateway_customer_id=customer_id)
        gateway_data = {
            **checkout_data,
            "value": preview["total_amount"],
            "totalValue": preview["total_amount"],
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
            locked_order.gateway_subscription_id = (
                str(response.get("id") or "")
                if plan_price.billing_model == PlanPrice.BillingModel.RECURRING
                else ""
            )
            locked_order.gateway_installment_id = str(response.get("installment") or "")
            locked_order.metadata = {
                **(locked_order.metadata or {}),
                "gateway_response": redact_sensitive_data(response),
                "provisioning_status": "COMPLETED",
            }
            locked_order.save()

            if created_new_subscription:
                locked_subscription.gateway_customer_id = customer_id
                locked_subscription.gateway_subscription_id = locked_order.gateway_subscription_id
                locked_subscription.gateway_status = str(response.get("status") or "")
                locked_subscription.metadata = {
                    **(locked_subscription.metadata or {}),
                    "provisioning_status": "COMPLETED",
                }
                locked_subscription.save()

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
        return CheckoutResult(order=locked_order, subscription=locked_subscription, created=True)
    except Exception as exc:
        with transaction.atomic():
            failed_order = BillingOrder.objects.select_for_update().get(pk=order.pk)
            failed_order.status = BillingOrder.Status.FAILED
            failed_order.failed_at = timezone.now()
            failed_order.metadata = {
                **(failed_order.metadata or {}),
                "provisioning_status": "FAILED",
                "error_code": exc.__class__.__name__,
            }
            failed_order.save(update_fields=["status", "failed_at", "metadata", "updated_at"])

            failed_subscription = Subscription.objects.select_for_update().get(pk=subscription.pk)
            if created_new_subscription and failed_subscription.status == Subscription.Status.PENDING:
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
            elif not created_new_subscription:
                pending_checkout = dict((failed_subscription.metadata or {}).get("pending_checkout") or {})
                if pending_checkout.get("order_public_id") == str(order.public_id):
                    pending_checkout["status"] = "FAILED"
                    failed_subscription.metadata = {
                        **(failed_subscription.metadata or {}),
                        "pending_checkout": pending_checkout,
                    }
                    failed_subscription.save(update_fields=["metadata", "updated_at"])
        raise
