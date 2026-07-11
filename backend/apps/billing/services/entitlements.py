from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from django.db import transaction
from django.utils import timezone

from apps.billing.models import Subscription


@dataclass(frozen=True, slots=True)
class EntitlementDecision:
    allowed: bool
    code: str
    message: str
    redirect_to: str
    subscription: Subscription | None = None
    trial_days_remaining: int | None = None


def has_admin_bypass(user) -> bool:
    """Libera apenas superusuários ou staff com papel administrativo explícito."""

    return bool(
        user
        and user.is_authenticated
        and (
            getattr(user, "is_superuser", False)
            or (
                getattr(user, "is_staff", False)
                and getattr(user, "is_admin_role", False)
            )
        )
    )


def _latest_subscription(user) -> Subscription | None:
    if not user or not user.is_authenticated:
        return None
    return (
        Subscription.objects.select_related("plan", "billing_order", "billing_order__plan_price")
        .filter(user=user)
        .order_by("-created_at")
        .first()
    )


def _expire_stale_trial(subscription: Subscription, now) -> Subscription:
    if (
        subscription.status == Subscription.Status.TRIALING
        and subscription.trial_ends_at
        and subscription.trial_ends_at < now
    ):
        with transaction.atomic():
            locked = Subscription.objects.select_for_update().get(pk=subscription.pk)
            if (
                locked.status == Subscription.Status.TRIALING
                and locked.trial_ends_at
                and locked.trial_ends_at < now
            ):
                locked.status = Subscription.Status.EXPIRED
                locked.access_ends_at = locked.access_ends_at or locked.trial_ends_at
                locked.save(update_fields=["status", "access_ends_at", "updated_at"])
            return locked
    return subscription


def get_entitlement(user, *, now=None) -> EntitlementDecision:
    now = now or timezone.now()

    if has_admin_bypass(user):
        return EntitlementDecision(
            allowed=True,
            code="ADMIN_BYPASS",
            message="Acesso administrativo autorizado.",
            redirect_to="/dashboard",
        )

    subscription = _latest_subscription(user)
    if not subscription:
        return EntitlementDecision(
            allowed=False,
            code="SUBSCRIPTION_REQUIRED",
            message="É necessário possuir uma assinatura ativa ou um teste gratuito válido.",
            redirect_to="/planos",
        )

    subscription = _expire_stale_trial(subscription, now)

    if subscription.status == Subscription.Status.TRIALING:
        if not subscription.trial_ends_at or subscription.trial_ends_at < now:
            return EntitlementDecision(
                allowed=False,
                code="TRIAL_EXPIRED",
                message="Seu teste gratuito expirou. Escolha um plano para continuar.",
                redirect_to="/planos?reason=trial_expired",
                subscription=subscription,
                trial_days_remaining=0,
            )
        seconds = max((subscription.trial_ends_at - now).total_seconds(), 0)
        return EntitlementDecision(
            allowed=True,
            code="TRIAL_ACTIVE",
            message="Teste gratuito ativo.",
            redirect_to="/dashboard",
            subscription=subscription,
            trial_days_remaining=ceil(seconds / 86400),
        )

    if subscription.status == Subscription.Status.ACTIVE:
        end_at = subscription.access_ends_at or subscription.current_period_end
        if end_at and end_at < now:
            return EntitlementDecision(
                allowed=False,
                code="SUBSCRIPTION_EXPIRED",
                message="Sua assinatura expirou. Renove o plano para continuar.",
                redirect_to="/planos?reason=subscription_expired",
                subscription=subscription,
            )
        return EntitlementDecision(
            allowed=True,
            code="SUBSCRIPTION_ACTIVE",
            message="Assinatura ativa.",
            redirect_to="/dashboard",
            subscription=subscription,
        )

    if subscription.status == Subscription.Status.PAST_DUE:
        if not subscription.grace_period_ends_at or subscription.grace_period_ends_at >= now:
            return EntitlementDecision(
                allowed=True,
                code="PAYMENT_GRACE_PERIOD",
                message="Pagamento em atraso dentro do período de tolerância.",
                redirect_to="/billing",
                subscription=subscription,
            )
        return EntitlementDecision(
            allowed=False,
            code="PAYMENT_PAST_DUE",
            message="Há um pagamento em atraso. Regularize a assinatura para continuar.",
            redirect_to="/billing?reason=past_due",
            subscription=subscription,
        )

    code_map = {
        Subscription.Status.PENDING: (
            "PAYMENT_PENDING",
            "A assinatura ainda aguarda confirmação do pagamento.",
            "/billing?reason=pending",
        ),
        Subscription.Status.SUSPENDED: (
            "SUBSCRIPTION_SUSPENDED",
            "Sua assinatura está suspensa. Regularize o pagamento para continuar.",
            "/billing?reason=suspended",
        ),
        Subscription.Status.CANCELED: (
            "SUBSCRIPTION_CANCELED",
            "Sua assinatura foi cancelada. Escolha um plano para continuar.",
            "/planos?reason=canceled",
        ),
        Subscription.Status.EXPIRED: (
            "SUBSCRIPTION_EXPIRED",
            "Seu acesso expirou. Escolha um plano para continuar.",
            "/planos?reason=expired",
        ),
    }
    code, message, redirect_to = code_map.get(
        subscription.status,
        (
            "SUBSCRIPTION_REQUIRED",
            "É necessário possuir uma assinatura ativa ou um teste gratuito válido.",
            "/planos",
        ),
    )
    return EntitlementDecision(
        allowed=False,
        code=code,
        message=message,
        redirect_to=redirect_to,
        subscription=subscription,
    )


def has_active_entitlement(user) -> bool:
    return get_entitlement(user).allowed
