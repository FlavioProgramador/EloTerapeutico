from __future__ import annotations

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from apps.billing.services.entitlements import get_entitlement, has_admin_bypass
from ..models import Communication, CommunicationAutomation, CommunicationPlanEntitlement, CommunicationTemplate
from .privacy import CommunicationLimitExceeded


def get_plan_communication_entitlement(owner) -> CommunicationPlanEntitlement | None:
    if has_admin_bypass(owner):
        return None
    entitlement = get_entitlement(owner)
    if not entitlement.allowed or not entitlement.subscription:
        return None
    plan = entitlement.subscription.plan
    communication_entitlement, _ = CommunicationPlanEntitlement.objects.get_or_create(plan=plan)
    return communication_entitlement


def _monthly_limit(owner) -> int | None:
    if has_admin_bypass(owner):
        return None
    entitlement = get_plan_communication_entitlement(owner)
    if entitlement is None:
        if not getattr(settings, "BILLING_REQUIRE_SUBSCRIPTION", True):
            return None
        return 0
    return entitlement.max_communications_per_month


def enforce_communication_access(owner) -> None:
    if not getattr(settings, "COMMUNICATIONS_ENABLED", True):
        raise PermissionDenied("O módulo de Comunicações está desativado.")
    if has_admin_bypass(owner):
        return
    entitlement = get_plan_communication_entitlement(owner)
    if entitlement is None:
        if not getattr(settings, "BILLING_REQUIRE_SUBSCRIPTION", True):
            return
        raise PermissionDenied("Seu plano atual não inclui o módulo de Comunicações.")
    if not entitlement.communications_enabled:
        raise PermissionDenied("Seu plano atual não inclui o módulo de Comunicações.")


def enforce_communication_limit(owner, *, channel: str | None = None) -> None:
    enforce_communication_access(owner)
    limit = _monthly_limit(owner)
    if limit is None:
        return
    if limit <= 0:
        raise CommunicationLimitExceeded()
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current = Communication.objects.filter(owner=owner, created_at__gte=month_start).exclude(status=Communication.Status.DRAFT).count()
    if current >= limit:
        raise CommunicationLimitExceeded()
    if channel == Communication.Channel.EMAIL:
        entitlement = get_plan_communication_entitlement(owner)
        email_limit = entitlement.max_email_communications_per_month if entitlement else 0
        if email_limit is not None:
            current_email = Communication.objects.filter(
                owner=owner,
                channel=Communication.Channel.EMAIL,
                created_at__gte=month_start,
            ).exclude(status=Communication.Status.DRAFT).count()
            if current_email >= email_limit:
                raise CommunicationLimitExceeded("Você atingiu o limite de comunicações por e-mail do seu plano atual.")


def enforce_template_creation(owner) -> None:
    enforce_communication_access(owner)
    if has_admin_bypass(owner):
        return
    entitlement = get_plan_communication_entitlement(owner)
    if entitlement is None or not entitlement.custom_templates_enabled:
        raise PermissionDenied("Seu plano atual não inclui templates personalizados.")
    limit = entitlement.max_custom_templates
    if limit is not None and CommunicationTemplate.objects.filter(owner=owner, is_archived=False).count() >= limit:
        raise CommunicationLimitExceeded("Você atingiu o limite de templates personalizados do seu plano atual.")


def enforce_automation_creation(owner) -> None:
    enforce_communication_access(owner)
    if has_admin_bypass(owner):
        return
    entitlement = get_plan_communication_entitlement(owner)
    if entitlement is None or not entitlement.automations_enabled:
        raise PermissionDenied("Seu plano atual não inclui automações de comunicação.")
    limit = entitlement.max_automations
    if limit is not None and CommunicationAutomation.objects.filter(owner=owner).count() >= limit:
        raise CommunicationLimitExceeded("Você atingiu o limite de automações do seu plano atual.")
