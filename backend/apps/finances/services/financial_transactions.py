"""Casos de uso de criação, edição e exclusão de transações."""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from apps.finances.exceptions import (
    FinancialOwnershipError,
    InvalidPaymentTransitionError,
)
from apps.finances.models import FinancialTransaction


def _resolve_therapist(*, actor, patient=None, current=None):
    if actor.is_therapist:
        return actor
    if patient is not None:
        return patient.therapist
    if current is not None:
        return current.therapist
    raise FinancialOwnershipError(
        "Não foi possível determinar o profissional proprietário da transação."
    )


def _validate_relationships(*, therapist, patient=None, appointment=None):
    if patient is not None and patient.therapist_id != therapist.pk:
        raise FinancialOwnershipError(
            {"patient": "Este paciente não pertence ao profissional informado."}
        )
    if appointment is not None and appointment.therapist_id != therapist.pk:
        raise FinancialOwnershipError(
            {"appointment": "Esta consulta não pertence ao profissional informado."}
        )
    if appointment is not None and patient is not None and appointment.patient_id != patient.pk:
        raise FinancialOwnershipError(
            {"appointment": "A consulta não pertence ao paciente informado."}
        )


@transaction.atomic
def create_financial_transaction(*, actor, validated_data: dict):
    data = dict(validated_data)
    patient = data.get("patient")
    appointment = data.get("appointment")
    therapist = _resolve_therapist(actor=actor, patient=patient)
    _validate_relationships(
        therapist=therapist, patient=patient, appointment=appointment
    )
    target_status = data.pop(
        "payment_status", FinancialTransaction.PaymentStatus.PENDING
    )
    data.pop("source", None)
    data.pop("subscription", None)
    data.pop("paid_amount", None)
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
                "payment_method", FinancialTransaction.PaymentMethod.PIX
            ),
            paid_at=data.get("paid_at"),
            amount=Decimal(str(current.amount)),
        )
    return current


@transaction.atomic
def update_financial_transaction(
    *, actor, financial_transaction, validated_data: dict
):
    current = FinancialTransaction.objects.select_for_update().get(
        pk=financial_transaction.pk
    )
    data = dict(validated_data)
    patient = data.get("patient", current.patient)
    appointment = data.get("appointment", current.appointment)
    therapist = _resolve_therapist(
        actor=actor, patient=patient, current=current
    )
    _validate_relationships(
        therapist=therapist, patient=patient, appointment=appointment
    )
    target_status = data.pop("payment_status", current.payment_status)
    for protected in ("therapist", "source", "subscription", "paid_amount"):
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
def delete_financial_transaction(*, actor, financial_transaction) -> None:
    current = FinancialTransaction.objects.select_for_update().get(
        pk=financial_transaction.pk
    )
    if actor.is_therapist and current.therapist_id != actor.pk:
        raise FinancialOwnershipError(
            "Esta transação não pertence ao profissional autenticado."
        )
    current.delete()
