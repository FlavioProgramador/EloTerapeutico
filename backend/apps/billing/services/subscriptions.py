import uuid
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.billing.models import Payment, Plan, PlanPrice, Subscription
from apps.billing.services.access import SubscriptionAccessService
from apps.billing.services.gateways.asaas import AsaasGateway
from apps.billing.services.orders import create_billing_order

ACTIVE_OR_BLOCKING_STATUSES = {
    Subscription.Status.TRIALING,
    Subscription.Status.PENDING,
    Subscription.Status.ACTIVE,
    Subscription.Status.PAST_DUE,
    Subscription.Status.SUSPENDED,
}


def get_gateway():
    return AsaasGateway()


def get_current_subscription(user):
    return (
        Subscription.objects.select_related("plan", "billing_order", "billing_order__plan_price")
        .filter(user=user, status__in=ACTIVE_OR_BLOCKING_STATUSES)
        .order_by("-created_at")
        .first()
    )


def _legacy_price_for_plan(plan: Plan) -> PlanPrice:
    price = plan.prices.filter(is_active=True).order_by("billing_interval", "total_amount").first()
    if price:
        return price
    interval = (
        PlanPrice.BillingInterval.YEARLY
        if plan.billing_cycle == Plan.BillingCycle.YEARLY
        else PlanPrice.BillingInterval.MONTHLY
    )
    return PlanPrice.objects.create(
        plan=plan,
        name=f"{plan.name} — {'Anual' if interval == PlanPrice.BillingInterval.YEARLY else 'Mensal'}",
        slug=f"{plan.slug}-{interval.lower()}-{uuid.uuid4().hex[:8]}",
        currency=plan.currency,
        total_amount=plan.price,
        billing_interval=interval,
        billing_model=PlanPrice.BillingModel.RECURRING,
        discount_percentage=Decimal("0.00"),
        installments_enabled=False,
        min_installments=1,
        max_installments=1,
        is_active=plan.is_active,
    )


def create_subscription_for_user(
    user,
    plan: Plan,
    checkout_data: dict[str, Any] | None = None,
) -> Subscription:
    """Compatibilidade com o endpoint legado, encaminhando a criação para BillingOrder."""
    if not plan.is_active:
        raise ValidationError("Este plano não está disponível para assinatura.")
    checkout_data = dict(checkout_data or {})
    plan_price = checkout_data.get("plan_price") or _legacy_price_for_plan(plan)
    checkout_data.setdefault("installmentCount", 1)
    idempotency_key = str(checkout_data.get("idempotency_key") or f"legacy-{user.pk}-{uuid.uuid4()}")
    _, subscription = create_billing_order(
        user=user,
        plan_price=plan_price,
        checkout_data=checkout_data,
        idempotency_key=idempotency_key,
    )
    return subscription


def activate_subscription_from_payment(subscription: Subscription, payment: Payment) -> Subscription:
    return SubscriptionAccessService.activate_from_payment(subscription, payment)


def mark_subscription_past_due(subscription: Subscription) -> Subscription:
    return SubscriptionAccessService.mark_past_due(subscription)


def schedule_subscription_cancellation(user) -> Subscription:
    subscription = get_current_subscription(user)
    if not subscription:
        raise ValidationError("Nenhuma assinatura operacional encontrada.")
    return SubscriptionAccessService.schedule_cancellation(subscription)


def resume_subscription_cancellation(user) -> Subscription:
    subscription = get_current_subscription(user)
    if not subscription:
        raise ValidationError("Nenhuma assinatura operacional encontrada.")
    return SubscriptionAccessService.resume_cancellation(subscription)


def cancel_subscription(user) -> Subscription:
    subscription = get_current_subscription(user)
    if not subscription:
        raise ValidationError("Nenhuma assinatura operacional encontrada para cancelamento.")

    if subscription.gateway_subscription_id:
        get_gateway().cancel_subscription(subscription.gateway_subscription_id)

    with transaction.atomic():
        locked = Subscription.objects.select_for_update().get(pk=subscription.pk)
        if locked.status in {Subscription.Status.CANCELED, Subscription.Status.EXPIRED}:
            return locked
        locked.status = Subscription.Status.CANCELED
        locked.cancel_at_period_end = False
        locked.canceled_at = timezone.now()
        locked.save(update_fields=["status", "cancel_at_period_end", "canceled_at", "updated_at"])
        if locked.billing_order_id:
            order = locked.billing_order
            order.status = order.Status.CANCELED
            order.canceled_at = timezone.now()
            order.save(update_fields=["status", "canceled_at", "updated_at"])
        return locked


def change_plan(user, new_plan: Plan) -> Subscription:
    """Registra a intenção sem cancelar o acesso atual antes do novo checkout."""
    if not new_plan.is_active:
        raise ValidationError("Este plano não está disponível para troca.")
    current = get_current_subscription(user)
    if not current:
        raise ValidationError("Nenhuma assinatura operacional encontrada. Inicie uma nova contratação.")
    if current.plan_id == new_plan.pk:
        raise ValidationError("Você já está neste plano.")

    with transaction.atomic():
        locked = Subscription.objects.select_for_update().get(pk=current.pk)
        locked.metadata = {
            **(locked.metadata or {}),
            "pending_plan_change": {
                "target_plan_id": new_plan.pk,
                "target_plan_slug": new_plan.slug,
                "status": "AWAITING_CHECKOUT",
                "requested_at": timezone.now().isoformat(),
            },
        }
        locked.save(update_fields=["metadata", "updated_at"])
        return locked
