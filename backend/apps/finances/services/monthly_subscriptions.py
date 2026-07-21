"""Casos de uso de mensalidades recorrentes de pacientes."""

from __future__ import annotations

from django.db import transaction

from apps.finances.exceptions import (
    FinancialOwnershipError,
    InvalidSubscriptionStatusError,
)
from apps.finances.models import FinancialTransaction, MonthlySubscription
from apps.organizations.models import OrganizationMembership

FINANCE_ROLES = {
    OrganizationMembership.Role.OWNER,
    OrganizationMembership.Role.ADMIN,
    OrganizationMembership.Role.FINANCE,
}


def _ensure_finance_access(*, actor, organization):
    if not OrganizationMembership.objects.filter(
        organization=organization,
        user=actor,
        status=OrganizationMembership.Status.ACTIVE,
        role__in=FINANCE_ROLES,
    ).exists():
        raise FinancialOwnershipError("Você não possui acesso financeiro nesta organização.")


def _resolve_therapist(*, actor, patient, current=None):
    therapist = actor if actor.is_therapist else patient.therapist
    if current is not None and current.therapist_id != therapist.pk:
        raise FinancialOwnershipError(
            "A mensalidade não pertence ao profissional autenticado."
        )
    if patient.therapist_id != therapist.pk:
        raise FinancialOwnershipError(
            {"patient": "Este paciente não pertence ao profissional informado."}
        )
    return therapist


def create_first_subscription_charge(*, subscription):
    if not subscription.first_due_date:
        return None
    charge, _ = FinancialTransaction.objects.get_or_create(
        organization=subscription.organization,
        subscription=subscription,
        due_date=subscription.first_due_date,
        defaults={
            "therapist": subscription.therapist,
            "patient": subscription.patient,
            "transaction_type": FinancialTransaction.TransactionType.INCOME,
            "category": FinancialTransaction.Category.SUBSCRIPTION,
            "source": FinancialTransaction.Source.SUBSCRIPTION,
            "amount": subscription.monthly_amount,
            "payment_method": subscription.preferred_payment_method,
            "payment_link": subscription.payment_link,
            "description": f"Mensalidade - {subscription.patient.full_name}",
        },
    )
    return charge


@transaction.atomic
def create_monthly_subscription(*, actor, validated_data: dict, organization=None):
    data = dict(validated_data)
    patient = data["patient"]
    organization = organization or patient.organization
    _ensure_finance_access(actor=actor, organization=organization)
    if patient.organization_id != organization.pk:
        raise FinancialOwnershipError(
            {"patient": "Este paciente pertence a outra organização."}
        )
    therapist = _resolve_therapist(actor=actor, patient=patient)
    data.pop("organization", None)
    data["organization"] = organization
    data["therapist"] = therapist
    probe = MonthlySubscription(**data)
    if not probe.next_billing_date:
        probe.next_billing_date = probe.first_due_date or probe.default_first_due_date()
    probe.full_clean()
    probe.save()
    create_first_subscription_charge(subscription=probe)
    return probe


@transaction.atomic
def update_monthly_subscription(
    *,
    actor,
    monthly_subscription,
    validated_data: dict,
    organization=None,
):
    current = MonthlySubscription.objects.select_for_update().select_related(
        "organization",
        "patient",
    ).get(pk=monthly_subscription.pk)
    organization = organization or current.organization
    _ensure_finance_access(actor=actor, organization=organization)
    if current.organization_id != organization.pk:
        raise FinancialOwnershipError("A mensalidade pertence a outra organização.")
    data = dict(validated_data)
    patient = data.get("patient", current.patient)
    if patient.organization_id != organization.pk:
        raise FinancialOwnershipError(
            {"patient": "Este paciente pertence a outra organização."}
        )
    _resolve_therapist(actor=actor, patient=patient, current=current)
    data.pop("organization", None)
    data.pop("therapist", None)
    for field, value in data.items():
        setattr(current, field, value)
    current.full_clean()
    current.save(update_fields=[*data.keys(), "updated_at"] if data else ["updated_at"])
    return current


@transaction.atomic
def change_monthly_subscription_status(
    *,
    actor,
    monthly_subscription,
    target_status: str,
    organization=None,
):
    current = MonthlySubscription.objects.select_for_update().select_related(
        "organization",
        "patient",
    ).get(pk=monthly_subscription.pk)
    organization = organization or current.organization
    _ensure_finance_access(actor=actor, organization=organization)
    if current.organization_id != organization.pk:
        raise FinancialOwnershipError("A mensalidade pertence a outra organização.")
    _resolve_therapist(actor=actor, patient=current.patient, current=current)
    allowed = {value for value, _ in MonthlySubscription.Status.choices}
    if target_status not in allowed:
        raise InvalidSubscriptionStatusError("Status de mensalidade inválido.")
    current.status = target_status
    current.save(update_fields=["status", "updated_at"])
    return current


@transaction.atomic
def advance_next_billing_date(*, monthly_subscription):
    current = MonthlySubscription.objects.select_for_update().get(
        pk=monthly_subscription.pk
    )
    current.next_billing_date = current.next_billing_date_after()
    current.save(update_fields=["next_billing_date", "updated_at"])
    return current
