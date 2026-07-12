from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.billing.models import PlanPrice, Subscription
from apps.users.models import User


def trial_duration_days() -> int:
    """Retorna a duração oficial do trial, definida exclusivamente no backend."""

    return max(int(getattr(settings, "BILLING_TRIAL_DAYS", 7)), 1)


@transaction.atomic
def start_trial(*, user: User, plan_price: PlanPrice) -> Subscription:
    """Inicia o único teste gratuito permitido para a conta.

    O bloqueio no usuário impede reinício por troca de plano, cancelamento ou
    nova tentativa de checkout. A operação é protegida por select_for_update.
    """

    locked_user = User.objects.select_for_update().get(pk=user.pk)
    if locked_user.trial_used_at is not None:
        raise ValidationError("O teste gratuito desta conta já foi utilizado.")

    previous_trial = Subscription.objects.filter(
        user=locked_user,
        metadata__trial_used=True,
    ).exists()
    if previous_trial:
        locked_user.trial_used_at = timezone.now()
        locked_user.save(update_fields=["trial_used_at"])
        raise ValidationError("O teste gratuito desta conta já foi utilizado.")

    now = timezone.now()
    trial_ends_at = now + timedelta(days=trial_duration_days())
    subscription = (
        Subscription.objects.select_for_update()
        .filter(user=locked_user, status=Subscription.Status.PENDING)
        .order_by("-created_at")
        .first()
    )
    if subscription is None:
        subscription = Subscription(user=locked_user, plan=plan_price.plan)

    subscription.plan = plan_price.plan
    subscription.status = Subscription.Status.TRIALING
    subscription.started_at = now
    subscription.access_starts_at = now
    subscription.access_ends_at = trial_ends_at
    subscription.trial_ends_at = trial_ends_at
    subscription.current_period_start = None
    subscription.current_period_end = None
    subscription.grace_period_ends_at = None
    subscription.cancel_at_period_end = False
    subscription.canceled_at = None
    subscription.metadata = {
        **(subscription.metadata or {}),
        "trial_used": True,
        "trial_days": trial_duration_days(),
        "trial_started_at": now.isoformat(),
        "selected_plan_price_id": plan_price.pk,
        "selected_plan_price_slug": plan_price.slug,
        "registration_mode": "TRIAL",
    }
    subscription.save()

    locked_user.trial_used_at = now
    locked_user.save(update_fields=["trial_used_at"])
    return subscription


@transaction.atomic
def expire_finished_trials(*, at=None) -> int:
    """Expira trials finalizados sem apagar dados da conta."""

    at = at or timezone.now()
    subscriptions = Subscription.objects.select_for_update().filter(
        status=Subscription.Status.TRIALING,
        trial_ends_at__lt=at,
    )
    updated = 0
    for subscription in subscriptions.iterator():
        subscription.status = Subscription.Status.EXPIRED
        subscription.access_ends_at = subscription.access_ends_at or subscription.trial_ends_at
        subscription.metadata = {
            **(subscription.metadata or {}),
            "trial_expired_at": at.isoformat(),
        }
        subscription.save(update_fields=["status", "access_ends_at", "metadata", "updated_at"])
        updated += 1
    return updated
