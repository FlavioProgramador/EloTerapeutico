"""Casos de uso de criação, edição e exclusão de transações."""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from apps.finances.exceptions import (
    FinancialOwnershipError,
    InvalidPaymentTransitionError,
)
from apps.finances.models import FinancialTransaction
from apps.organizations.models import OrganizationMembership

FINANCE_ROLES = {
    OrganizationMembership.Role.OWNER,
    OrganizationMembership.Role.ADMIN,
    OrganizationMembership.Role.FINANCE,
}


def _resolve_therapist(*, actor, patient=None, current=None):
    if actor.is_therapist:
        return actor
    if patient is not None:
        return patient.therapist
    if current is not None:
        return current.therapist
    raise FinancialOwnershipError(
        "Não foi possível determinar o profissional responsável pela transação."
    )


def _resolve_organization(*, actor, organization=None, patient=None, appointment=None, current=None):
    if organization is not None:
        resolved = organization
    elif current is not None:
        resolved = current.organization
    elif appointment is not None:
        resolved = appointment.organization
    elif patient is not None:
        resolved = patient.organization
    else:
        memberships = OrganizationMembership.objects.filter(
            user=actor,
            status=OrganizationMembership.Status.ACTIVE,
            role__in=FINANCE_ROLES,
        ).select_related("organization")
        resolved_membership = memberships.filter(is_default=True).first()
        if resolved_membership is None:
            first_two = list(memberships[:2])
            resolved_membership = first_two[0] if len(first_two) == 1 else None
        if resolved_membership is None:
            raise FinancialOwnershipError("Selecione uma organização para operar o financeiro.")
        resolved = resolved_membership.organization

    allowed = OrganizationMembership.objects.filter(
        organization=resolved,
        user=actor,
        status=OrganizationMembership.Status.ACTIVE,
        role__in=FINANCE_ROLES,
    ).exists()
    if not allowed:
        raise FinancialOwnershipError("Você não possui acesso financeiro nesta organização.")
    return resolved


def _validate_relationships(*, organization, therapist, patient=None, appointment=None):
    if patient is not None:
        if patient.organization_id != organization.pk:
            raise FinancialOwnershipError({"patient": "Este paciente pertence a outra organização."})
        if patient.therapist_id != therapist.pk:
            raise FinancialOwnershipError({"patient": "Este paciente não pertence ao profissional informado."})
    if appointment is not None:
        if appointment.organization_id != organization.pk:
            raise FinancialOwnershipError({"appointment": "Esta consulta pertence a outra organização."})
        if appointment.therapist_id != therapist.pk:
            raise FinancialOwnershipError({"appointment": "Esta consulta não pertence ao profissional informado."})
        if patient is not None and appointment.patient_id != patient.pk:
            raise FinancialOwnershipError({"appointment": "A consulta não pertence ao paciente informado."})


@transaction.atomic
def create_financial_transaction(*, actor, validated_data: dict, organization=None):
    data = dict(validated_data)
    patient = data.get("patient")
    appointment = data.get("appointment")
    organization = _resolve_organization(
        actor=actor,
        organization=organization,
        patient=patient,
        appointment=appointment,
    )
    therapist = _resolve_therapist(actor=actor, patient=patient)
    _validate_relationships(
        organization=organization,
        therapist=therapist,
        patient=patient,
        appointment=appointment,
    )
    target_status = data.pop(
        "payment_status",
        FinancialTransaction.PaymentStatus.PENDING,
    )
    data.pop("source", None)
    data.pop("subscription", None)
    data.pop("paid_amount", None)
    data.pop("organization", None)
    data["organization"] = organization
    data["therapist"] = therapist
    data["payment_status"] = FinancialTransaction.PaymentStatus.PENDING
    current = FinancialTransaction(**data)
    current.full_clean()
    current.save()
    if target_status not in {
        FinancialTransaction.PaymentStatus.PENDING,
        FinancialTransaction.PaymentStatus.PAID,
    }:
        raise InvalidPaymentTransitionError(
            {"payment_status": "O status inicial deve ser pendente ou pago."}
        )
    if target_status == FinancialTransaction.PaymentStatus.PAID:
        from apps.finances.services.payments import register_payment

        current = register_payment(
            financial_transaction=current,
            payment_method=data.get(
                "payment_method",
                FinancialTransaction.PaymentMethod.PIX,
            ),
            paid_at=data.get("paid_at"),
            amount=Decimal(str(current.amount)),
        )
    return current


@transaction.atomic
def update_financial_transaction(
    *,
    actor,
    financial_transaction,
    validated_data: dict,
    organization=None,
):
    current = FinancialTransaction.objects.select_for_update().select_related(
        "organization",
        "patient",
        "appointment",
    ).get(pk=financial_transaction.pk)
    organization = _resolve_organization(
        actor=actor,
        organization=organization,
        current=current,
    )
    if current.organization_id != organization.pk:
        raise FinancialOwnershipError("Esta transação pertence a outra organização.")
    data = dict(validated_data)
    patient = data.get("patient", current.patient)
    appointment = data.get("appointment", current.appointment)
    therapist = _resolve_therapist(actor=actor, patient=patient, current=current)
    _validate_relationships(
        organization=organization,
        therapist=therapist,
        patient=patient,
        appointment=appointment,
    )
    target_status = data.pop("payment_status", current.payment_status)
    for protected in (
        "organization",
        "therapist",
        "source",
        "subscription",
        "paid_amount",
    ):
        data.pop(protected, None)
    for field, value in data.items():
        setattr(current, field, value)
    current.full_clean()
    current.save(update_fields=[*data.keys(), "updated_at"] if data else ["updated_at"])
    if target_status != current.payment_status:
        if target_status == FinancialTransaction.PaymentStatus.PAID:
            from apps.finances.services.payments import register_payment

            return register_payment(
                financial_transaction=current,
                payment_method=current.payment_method,
                paid_at=current.paid_at,
            )
        if target_status == FinancialTransaction.PaymentStatus.CANCELLED:
            from apps.finances.services.cancellations import cancel_transaction

            return cancel_transaction(financial_transaction=current)
        if target_status == FinancialTransaction.PaymentStatus.REFUNDED:
            from apps.finances.services.refunds import refund_transaction

            return refund_transaction(financial_transaction=current)
        raise InvalidPaymentTransitionError(
            {"payment_status": "Use a ação financeira apropriada para alterar o status."}
        )
    return current


@transaction.atomic
def delete_financial_transaction(*, actor, financial_transaction, organization=None) -> None:
    current = FinancialTransaction.objects.select_for_update().select_related(
        "organization"
    ).get(pk=financial_transaction.pk)
    resolved = _resolve_organization(
        actor=actor,
        organization=organization,
        current=current,
    )
    if current.organization_id != resolved.pk:
        raise FinancialOwnershipError("Esta transação pertence a outra organização.")
    current.delete()
