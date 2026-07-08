from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.billing.models import Subscription

FEATURE_FIELD_MAP = {
    "agenda": "has_agenda",
    "patients": "has_patients",
    "clinical_records": "has_clinical_records",
    "financial": "has_financial",
    "documents": "has_documents",
    "forms": "has_forms",
    "reports": "has_reports",
    "ai": "has_ai",
}

GRACE_PERIOD_DAYS = 3


def get_current_subscription(user):
    if not user or user.is_anonymous:
        return None
    return (
        Subscription.objects.select_related("plan")
        .filter(
            user=user,
            status__in=[
                Subscription.Status.TRIALING,
                Subscription.Status.ACTIVE,
                Subscription.Status.PAST_DUE,
            ],
        )
        .order_by("-created_at")
        .first()
    )


def is_subscription_usable(subscription: Subscription | None) -> bool:
    if not subscription:
        return False
    now = timezone.now()
    if subscription.status == Subscription.Status.ACTIVE:
        return not subscription.current_period_end or subscription.current_period_end >= now
    if subscription.status == Subscription.Status.TRIALING:
        return bool(subscription.trial_ends_at and subscription.trial_ends_at >= now)
    if subscription.status == Subscription.Status.PAST_DUE and subscription.current_period_end:
        return subscription.current_period_end + timedelta(days=GRACE_PERIOD_DAYS) >= now
    return False


def has_feature(user, feature_key: str) -> bool:
    if getattr(user, "is_superuser", False) or getattr(user, "is_admin_role", False):
        return True
    field_name = FEATURE_FIELD_MAP.get(feature_key)
    if not field_name:
        return False
    subscription = get_current_subscription(user)
    if not is_subscription_usable(subscription):
        return False
    return bool(getattr(subscription.plan, field_name, False))


def can_use_feature(user, feature_key: str) -> bool:
    return has_feature(user, feature_key)


def get_plan_limits(user) -> dict[str, int | None]:
    subscription = get_current_subscription(user)
    if not is_subscription_usable(subscription):
        return {"max_patients": 0, "max_storage_mb": 0}
    return {
        "max_patients": subscription.plan.max_patients,
        "max_storage_mb": subscription.plan.max_storage_mb,
    }


def enforce_patient_limit(user) -> None:
    if getattr(user, "is_superuser", False) or getattr(user, "is_admin_role", False):
        return
    if not can_use_feature(user, "patients"):
        raise ValidationError("Seu plano atual não permite cadastrar pacientes. Escolha ou altere seu plano.")
    limits = get_plan_limits(user)
    max_patients = limits.get("max_patients")
    if max_patients is None:
        return
    from apps.patients.models import Patient

    current_count = Patient.objects.filter(therapist=user).count()
    if current_count >= max_patients:
        raise ValidationError("Limite de pacientes atingido para o plano atual. Faça upgrade para continuar.")
