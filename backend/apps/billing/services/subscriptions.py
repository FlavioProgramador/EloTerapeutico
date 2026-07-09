from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.billing.models import Payment, Plan, Subscription
from apps.billing.services.gateways.asaas import AsaasGateway

ACTIVE_OR_BLOCKING_STATUSES = {
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


def create_subscription_for_user(user, plan: Plan) -> Subscription:
    if not plan.is_active:
        raise ValidationError("Este plano não está disponível para assinatura.")

    if get_current_subscription(user):
        raise ValidationError("Você já possui uma assinatura ativa, em teste, pendente ou em atraso.")

    with transaction.atomic():
        last_subscription = Subscription.objects.filter(user=user).order_by("-created_at").first()
        customer_id = last_subscription.gateway_customer_id if last_subscription else ""
        gateway = get_gateway()
        if not customer_id:
            customer = gateway.create_customer(user)
            customer_id = customer.get("id", "")
        gateway_subscription = gateway.create_subscription(user, plan, customer_id=customer_id)
        gateway_subscription_id = gateway_subscription.get("id", "")
        if not gateway_subscription_id:
            raise ValidationError("Gateway não retornou o identificador da assinatura.")

        now = timezone.now()
        trial_days = max(int(settings.BILLING_TRIAL_DAYS), 0)
        trial_ends_at = now + timedelta(days=trial_days) if trial_days else None
        status = Subscription.Status.TRIALING if trial_ends_at else Subscription.Status.PENDING
        return Subscription.objects.create(
            user=user,
            plan=plan,
            status=status,
            started_at=now,
            trial_ends_at=trial_ends_at,
            current_period_start=now if status == Subscription.Status.TRIALING else None,
            current_period_end=trial_ends_at,
            gateway_customer_id=customer_id,
            gateway_subscription_id=gateway_subscription_id,
            gateway_status=gateway_subscription.get("status", ""),
            metadata={"gateway_response": gateway_subscription},
        )


def _next_period_end(subscription: Subscription, start):
    if subscription.plan.billing_cycle == Plan.BillingCycle.YEARLY:
        return start + timedelta(days=365)
    return start + timedelta(days=30)


def activate_subscription_from_payment(subscription: Subscription, payment: Payment) -> Subscription:
    paid_at = payment.paid_at or timezone.now()
    subscription.status = Subscription.Status.ACTIVE
    subscription.started_at = subscription.started_at or paid_at
    subscription.current_period_start = paid_at
    subscription.current_period_end = _next_period_end(subscription, paid_at)
    subscription.canceled_at = None
    subscription.save(
        update_fields=[
            "status",
            "started_at",
            "current_period_start",
            "current_period_end",
            "canceled_at",
            "updated_at",
        ]
    )
    if payment.status not in {Payment.Status.CONFIRMED, Payment.Status.RECEIVED}:
        payment.status = Payment.Status.CONFIRMED
        payment.paid_at = paid_at
        payment.save(update_fields=["status", "paid_at", "updated_at"])
    return subscription


def mark_subscription_past_due(subscription: Subscription) -> Subscription:
    subscription.status = Subscription.Status.PAST_DUE
    subscription.save(update_fields=["status", "updated_at"])
    return subscription


def cancel_subscription(user) -> Subscription:
    subscription = get_current_subscription(user)
    if not subscription:
        raise ValidationError("Nenhuma assinatura ativa encontrada para cancelamento.")
    if subscription.gateway_subscription_id:
        get_gateway().cancel_subscription(subscription.gateway_subscription_id)
    subscription.status = Subscription.Status.CANCELED
    subscription.canceled_at = timezone.now()
    subscription.save(update_fields=["status", "canceled_at", "updated_at"])
    return subscription


def change_plan(user, new_plan: Plan) -> Subscription:
    if not new_plan.is_active:
        raise ValidationError("Este plano não está disponível para troca.")
    current = get_current_subscription(user)
    if current and current.plan_id == new_plan.pk:
        raise ValidationError("Você já está neste plano.")
    if current:
        cancel_subscription(user)
    return create_subscription_for_user(user, new_plan)
