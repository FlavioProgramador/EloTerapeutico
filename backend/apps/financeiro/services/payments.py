"""Registro transacional de pagamentos."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ..models import FinancialTransaction


@transaction.atomic
def mark_as_paid(*, financial_transaction, payment_method, paid_at=None, amount=None):
    current = (
        FinancialTransaction.objects.select_for_update().select_related("appointment").get(pk=financial_transaction.pk)
    )
    if not current.can_pay():
        raise ValidationError("Esta transação não está pendente de pagamento.")

    payment_amount = Decimal(amount) if amount is not None else current.outstanding_amount
    if payment_amount <= 0 or payment_amount > current.outstanding_amount:
        raise ValidationError("O valor informado para pagamento é inválido.")

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

    appointment = current.appointment
    if (
        appointment
        and current.payment_status == FinancialTransaction.PaymentStatus.PAID
        and appointment.status == appointment.Status.SCHEDULED
    ):
        appointment.status = appointment.Status.CONFIRMED
        appointment.save(update_fields=["status", "updated_at"])
    return current
