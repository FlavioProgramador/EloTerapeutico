"""Registro transacional de pagamentos."""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.finances.exceptions import (
    InvalidPaymentAmountError,
    InvalidPaymentTransitionError,
)
from apps.finances.integrations.scheduling import confirm_appointment_after_payment
from apps.finances.models import FinancialTransaction


@transaction.atomic
def register_payment(
    *, financial_transaction, payment_method, paid_at=None, amount=None
):
    current = FinancialTransaction.objects.select_for_update().get(
        pk=financial_transaction.pk
    )
    if not current.can_pay():
        raise InvalidPaymentTransitionError(
            "Esta transação não está pendente de pagamento."
        )
    payment_amount = (
        Decimal(str(amount)) if amount is not None else current.outstanding_amount
    )
    if payment_amount <= 0 or payment_amount > current.outstanding_amount:
        raise InvalidPaymentAmountError(
            "O valor informado para pagamento é inválido."
        )
    current.paid_amount += payment_amount
    current.payment_method = payment_method
    current.paid_at = paid_at or timezone.now()
    current.payment_status = (
        FinancialTransaction.PaymentStatus.PAID
        if current.paid_amount == current.amount
        else FinancialTransaction.PaymentStatus.PARTIAL
    )
    current.save(
        update_fields=[
            "paid_amount",
            "payment_status",
            "payment_method",
            "paid_at",
            "updated_at",
        ]
    )
    if current.payment_status == FinancialTransaction.PaymentStatus.PAID:
        confirm_appointment_after_payment(appointment_id=current.appointment_id)
    return current


mark_as_paid = register_payment

__all__ = ["mark_as_paid", "register_payment"]
