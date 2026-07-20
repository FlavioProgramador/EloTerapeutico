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
    onboarding_required: bool = False


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


def _onboarding_required(user) -> bool:
    return bool(
        user
        and user.is_authenticated
        and not getattr(user, "onboarding_completed", False)
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
                locked.metadata = {
                    **(locked.metadata or {}),
                    "trial_expired_at": now.isoformat(),
                }
                locked.save(
                    update_fields=["status", "access_ends_at", "metadata", "updated_at"]
                )
            return locked
    return subscription


def _expire_finished_subscription(subscription: Subscription, now) -> Subscription:
    end_at = subscription.access_ends_at or subscription.current_period_end
    if subscription.status == Subscription.Status.ACTIVE and end_at and end_at < now:
        with transaction.atomic():
            locked = Subscription.objects.select_for_update().get(pk=subscription.pk)
            locked_end = locked.access_ends_at or locked.current_period_end
            if locked.status == Subscription.Status.ACTIVE and locked_end and locked_end < now:
                locked.status = Subscription.Status.EXPIRED
                locked.metadata = {
                    **(locked.metadata or {}),
                    "subscription_expired_at": now.isoformat(),
                }
                locked.save(update_fields=["status", "metadata", "updated_at"])
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

    onboarding_required = _onboarding_required(user)
    subscription = _latest_subscription(user)
    if not subscription:
        return EntitlementDecision(
            allowed=False,
            code="SUBSCRIPTION_REQUIRED",
            message="Escolha um plano ou inicie o teste gratuito para liberar as ferramentas.",
            redirect_to="/planos",
            onboarding_required=onboarding_required,
        )

    subscription = _expire_stale_trial(subscription, now)
    subscription = _expire_finished_subscription(subscription, now)

    if subscription.status == Subscription.Status.TRIALING:
        if not subscription.trial_ends_at or subscription.trial_ends_at <= now:
            return EntitlementDecision(
                allowed=False,
                code="TRIAL_EXPIRED",
                message="Seu teste gratuito expirou. Escolha um plano para continuar.",
                redirect_to="/billing/expired",
                subscription=subscription,
                trial_days_remaining=0,
                onboarding_required=onboarding_required,
            )
        seconds = max((subscription.trial_ends_at - now).total_seconds(), 0)
        return EntitlementDecision(
            allowed=True,
            code="TRIAL_ACTIVE",
            message="Teste gratuito ativo.",
            redirect_to="/onboarding" if onboarding_required else "/dashboard",
            subscription=subscription,
            trial_days_remaining=ceil(seconds / 86400),
            onboarding_required=onboarding_required,
        )

    if subscription.status == Subscription.Status.ACTIVE:
        return EntitlementDecision(
            allowed=True,
            code="SUBSCRIPTION_ACTIVE",
            message="Assinatura ativa.",
            redirect_to="/onboarding" if onboarding_required else "/dashboard",
            subscription=subscription,
            onboarding_required=onboarding_required,
        )

    if (
        subscription.status == Subscription.Status.EXPIRED
        and (subscription.metadata or {}).get("trial_expired_at")
    ):
        return EntitlementDecision(
            allowed=False,
            code="TRIAL_EXPIRED",
            message="Seu teste gratuito expirou. Escolha um plano para continuar.",
            redirect_to="/billing/expired",
            subscription=subscription,
            trial_days_remaining=0,
            onboarding_required=onboarding_required,
        )

    code_map: dict[str, tuple[str, str, str]] = {
        Subscription.Status.PENDING: (
            "PAYMENT_PENDING",
            "A assinatura ainda aguarda confirmação do pagamento.",
            "/billing/pending",
        ),
        Subscription.Status.PAST_DUE: (
            "PAYMENT_PAST_DUE",
            "Há um pagamento em atraso. Regularize a assinatura para continuar.",
            "/billing/past-due",
        ),
        Subscription.Status.SUSPENDED: (
            "SUBSCRIPTION_SUSPENDED",
            "Sua assinatura está suspensa. Entre em contato com o suporte ou regularize a cobrança.",
            "/billing/past-due",
        ),
        Subscription.Status.CANCELED: (
            "SUBSCRIPTION_CANCELED",
            "Sua assinatura foi cancelada. Escolha um plano para reativar a conta.",
            "/billing/expired",
        ),
        Subscription.Status.EXPIRED: (
            "SUBSCRIPTION_EXPIRED",
            "Seu acesso expirou. Escolha um plano para continuar.",
            "/billing/expired",
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
        onboarding_required=onboarding_required,
    )


def has_active_entitlement(user) -> bool:
    return get_entitlement(user).allowed
