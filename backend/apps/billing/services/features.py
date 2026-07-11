from django.conf import settings
from django.core.exceptions import ValidationError

from apps.billing.models import Subscription
from apps.billing.services.entitlements import get_entitlement, has_admin_bypass

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


def get_current_subscription(user):
    return get_entitlement(user).subscription


def is_subscription_usable(subscription: Subscription | None) -> bool:
    if not subscription:
        return False
    return bool(subscription.has_access)


def has_feature(user, feature_key: str) -> bool:
    if has_admin_bypass(user):
        return True

    field_name = FEATURE_FIELD_MAP.get(feature_key)
    if not field_name:
        return False

    entitlement = get_entitlement(user)
    if not entitlement.allowed or not entitlement.subscription:
        return False

    # Pacientes são uma função-base do produto e devem existir em todos os
    # planos pagos e durante o teste gratuito. Limites quantitativos continuam
    # sendo aplicados separadamente quando estiverem configurados no plano.
    if feature_key == "patients":
        return True

    return bool(getattr(entitlement.subscription.plan, field_name, False))


def can_use_feature(user, feature_key: str) -> bool:
    return has_feature(user, feature_key)


def get_plan_limits(user) -> dict[str, int | None]:
    if has_admin_bypass(user):
        return {"max_patients": None, "max_storage_mb": None}

    entitlement = get_entitlement(user)
    if not entitlement.allowed or not entitlement.subscription:
        return {"max_patients": 0, "max_storage_mb": 0}

    return {
        "max_patients": entitlement.subscription.plan.max_patients,
        "max_storage_mb": entitlement.subscription.plan.max_storage_mb,
    }


def enforce_patient_limit(user) -> None:
    entitlement = get_entitlement(user)
    require_subscription = getattr(settings, "BILLING_REQUIRE_SUBSCRIPTION", True)

    # A suíte geral testa regras clínicas e multi-tenant sem montar billing em
    # todos os cenários. Quando existe assinatura, os limites continuam ativos.
    if not entitlement.allowed:
        if not require_subscription and entitlement.subscription is None:
            return
        raise ValidationError(entitlement.message)

    if has_admin_bypass(user):
        return

    # A ausência de configuração explícita desativa o limite. Nenhum plano é
    # impedido de cadastrar pacientes apenas por feature flag.
    if not getattr(settings, "BILLING_ENFORCE_PATIENT_LIMITS", True):
        return

    limits = get_plan_limits(user)
    max_patients = limits.get("max_patients")
    if max_patients is None:
        return

    from apps.patients.models import Patient

    current_count = Patient.objects.filter(therapist=user).count()
    if current_count >= max_patients:
        raise ValidationError(
            f"Limite de pacientes atingido para o plano atual ({current_count}/{max_patients}). "
            "Faça upgrade para continuar."
        )
