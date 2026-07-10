import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.billing.models import Payment, Plan, Subscription
from apps.billing.services.gateways.asaas import AsaasGateway

logger = logging.getLogger(__name__)

ACTIVE_OR_BLOCKING_STATUSES = {
    Subscription.Status.TRIALING,
    Subscription.Status.PENDING,
    Subscription.Status.ACTIVE,
    Subscription.Status.PAST_DUE,
}

ACTIVATABLE_SUBSCRIPTION_STATUSES = {
    Subscription.Status.TRIALING,
    Subscription.Status.PENDING,
    Subscription.Status.ACTIVE,
    Subscription.Status.PAST_DUE,
}


def get_gateway():
    return AsaasGateway()


def get_current_subscription(user):
    return (
        Subscription.objects.select_related("plan")
        .filter(user=user, status__in=ACTIVE_OR_BLOCKING_STATUSES)
        .order_by("-created_at")
        .first()
    )


def _safe_checkout_snapshot(checkout_data: dict[str, Any] | None) -> dict[str, Any]:
    if not checkout_data:
        return {}
    blocked_keys = {"plan", "cpfCnpj", "creditCardToken", "creditCard", "creditCardHolderInfo", "remoteIp"}
    snapshot: dict[str, Any] = {}
    for key, value in checkout_data.items():
        if key in blocked_keys:
            continue
        if isinstance(value, (datetime, date)):
            snapshot[key] = value.isoformat()
        elif isinstance(value, Decimal):
            snapshot[key] = str(value)
        else:
            snapshot[key] = value
    return snapshot


def _mark_provisioning_failed(subscription_id: int, exc: Exception) -> None:
    with transaction.atomic():
        subscription = Subscription.objects.select_for_update().get(pk=subscription_id)
        if subscription.status != Subscription.Status.PENDING:
            return
        subscription.status = Subscription.Status.CANCELED
        subscription.canceled_at = timezone.now()
        subscription.metadata = {
            **(subscription.metadata or {}),
            "provisioning_status": "FAILED",
            "provisioning_error_code": exc.__class__.__name__,
        }
        subscription.save(
            update_fields=[
                "status",
                "canceled_at",
                "metadata",
                "updated_at",
            ]
        )


def _cancel_remote_subscription_safely(gateway, gateway_subscription_id: str) -> None:
    if not gateway_subscription_id:
        return
    try:
        gateway.cancel_subscription(gateway_subscription_id)
    except Exception as exc:  # pragma: no cover - proteção operacional de compensação
        logger.warning(
            "billing_remote_subscription_compensation_failed",
            extra={"exception_type": exc.__class__.__name__},
        )


def create_subscription_for_user(user, plan: Plan, checkout_data: dict[str, Any] | None = None) -> Subscription:
    """Cria uma intenção local, provisiona no gateway fora da transação e finaliza sob lock."""
    if not plan.is_active:
        raise ValidationError("Este plano não está disponível para assinatura.")

    user_model = get_user_model()
    with transaction.atomic():
        locked_user = user_model.objects.select_for_update().get(pk=user.pk)
        if get_current_subscription(locked_user):
            raise ValidationError("Você já possui uma assinatura ativa, em teste, pendente ou em atraso.")

        last_subscription = Subscription.objects.filter(user=locked_user).order_by("-created_at").first()
        customer_id = last_subscription.gateway_customer_id if last_subscription else ""
        local_subscription = Subscription.objects.create(
            user=locked_user,
            plan=plan,
            status=Subscription.Status.PENDING,
            gateway_customer_id=customer_id,
            metadata={
                "checkout": _safe_checkout_snapshot(checkout_data),
                "provisioning_status": "PENDING",
                "activation_rule": "ACTIVE somente após webhook Asaas de pagamento confirmado ou recebido.",
            },
        )

    gateway = get_gateway()
    gateway_subscription_id = ""
    try:
        if not customer_id:
            customer = gateway.create_customer(user, checkout_data)
            customer_id = customer.get("id", "")
        if not customer_id:
            raise ValidationError("Gateway não retornou o identificador do cliente.")

        gateway_subscription = gateway.create_subscription(
            user,
            plan,
            checkout_data=checkout_data,
            customer_id=customer_id,
        )
        gateway_subscription_id = gateway_subscription.get("id", "")
        if not gateway_subscription_id:
            raise ValidationError("Gateway não retornou o identificador da assinatura.")

        with transaction.atomic():
            subscription = Subscription.objects.select_for_update().get(pk=local_subscription.pk)
            if subscription.status != Subscription.Status.PENDING:
                raise ValidationError("A intenção de assinatura não está mais disponível para finalização.")
            subscription.gateway_customer_id = customer_id
            subscription.gateway_subscription_id = gateway_subscription_id
            subscription.gateway_status = gateway_subscription.get("status", "")
            subscription.metadata = {
                **(subscription.metadata or {}),
                "gateway_response": gateway_subscription,
                "provisioning_status": "COMPLETED",
            }
            subscription.save(
                update_fields=[
                    "gateway_customer_id",
                    "gateway_subscription_id",
                    "gateway_status",
                    "metadata",
                    "updated_at",
                ]
            )
            return subscription
    except Exception as exc:
        _cancel_remote_subscription_safely(gateway, gateway_subscription_id)
        _mark_provisioning_failed(local_subscription.pk, exc)
        raise


def _next_period_end(subscription: Subscription, start):
    if subscription.plan.billing_cycle == Plan.BillingCycle.YEARLY:
        return start + timedelta(days=365)
    return start + timedelta(days=30)


@transaction.atomic
def activate_subscription_from_payment(subscription: Subscription, payment: Payment) -> Subscription:
    """Ativa uma assinatura uma única vez para cada pagamento do gateway."""
    locked_subscription = (
        Subscription.objects.select_for_update()
        .select_related("plan")
        .get(pk=subscription.pk)
    )
    locked_payment = Payment.objects.select_for_update().get(pk=payment.pk)

    if locked_payment.subscription_id != locked_subscription.pk or locked_payment.user_id != locked_subscription.user_id:
        raise ValidationError("Pagamento não pertence à assinatura informada.")
    if locked_subscription.status not in ACTIVATABLE_SUBSCRIPTION_STATUSES:
        raise ValidationError("A assinatura não permite ativação neste estado.")

    activation_key = locked_payment.gateway_payment_id or f"local:{locked_payment.pk}"
    metadata = dict(locked_subscription.metadata or {})
    if metadata.get("last_activated_payment_id") == activation_key:
        return locked_subscription

    paid_at = locked_payment.paid_at or timezone.now()
    locked_subscription.status = Subscription.Status.ACTIVE
    locked_subscription.started_at = locked_subscription.started_at or paid_at
    locked_subscription.current_period_start = paid_at
    locked_subscription.current_period_end = _next_period_end(locked_subscription, paid_at)
    locked_subscription.canceled_at = None
    locked_subscription.metadata = {
        **metadata,
        "last_activated_payment_id": activation_key,
        "last_activated_at": timezone.now().isoformat(),
    }
    locked_subscription.save(
        update_fields=[
            "status",
            "started_at",
            "current_period_start",
            "current_period_end",
            "canceled_at",
            "metadata",
            "updated_at",
        ]
    )

    if locked_payment.status not in {Payment.Status.CONFIRMED, Payment.Status.RECEIVED}:
        locked_payment.status = Payment.Status.CONFIRMED
        locked_payment.paid_at = paid_at
        locked_payment.save(update_fields=["status", "paid_at", "updated_at"])
    return locked_subscription


@transaction.atomic
def mark_subscription_past_due(subscription: Subscription) -> Subscription:
    locked_subscription = Subscription.objects.select_for_update().get(pk=subscription.pk)
    if locked_subscription.status in {
        Subscription.Status.CANCELED,
        Subscription.Status.EXPIRED,
    }:
        return locked_subscription
    locked_subscription.status = Subscription.Status.PAST_DUE
    locked_subscription.save(update_fields=["status", "updated_at"])
    return locked_subscription


def cancel_subscription(user) -> Subscription:
    subscription = get_current_subscription(user)
    if not subscription:
        raise ValidationError("Nenhuma assinatura ativa encontrada para cancelamento.")

    if subscription.gateway_subscription_id:
        get_gateway().cancel_subscription(subscription.gateway_subscription_id)

    with transaction.atomic():
        locked_subscription = Subscription.objects.select_for_update().get(pk=subscription.pk)
        if locked_subscription.status in {
            Subscription.Status.CANCELED,
            Subscription.Status.EXPIRED,
        }:
            return locked_subscription
        locked_subscription.status = Subscription.Status.CANCELED
        locked_subscription.canceled_at = timezone.now()
        locked_subscription.save(update_fields=["status", "canceled_at", "updated_at"])
        return locked_subscription


def change_plan(user, new_plan: Plan) -> Subscription:
    if not new_plan.is_active:
        raise ValidationError("Este plano não está disponível para troca.")
    current = get_current_subscription(user)
    if current and current.plan_id == new_plan.pk:
        raise ValidationError("Você já está neste plano.")
    if current:
        cancel_subscription(user)
    return create_subscription_for_user(user, new_plan)
