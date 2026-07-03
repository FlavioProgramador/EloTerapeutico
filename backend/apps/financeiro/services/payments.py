"""Registro transacional de pagamentos."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ..models import FinancialTransaction


@transaction.atomic
def mark_as_paid(*, financial_transaction, payment_method, paid_at=None):
    current = (
        FinancialTransaction.objects.select_for_update()
        .select_related("appointment")
        .get(pk=financial_transaction.pk)
    )
    if not current.can_pay():
        raise ValidationError("Esta transação não está pendente de pagamento.")

    current.payment_status = FinancialTransaction.PaymentStatus.PAID
    current.payment_method = payment_method
    current.paid_at = paid_at or timezone.now()
    current.save(
        update_fields=["payment_status", "payment_method", "paid_at", "updated_at"]
    )

    appointment = current.appointment
    if appointment and appointment.status == appointment.Status.SCHEDULED:
        appointment.status = appointment.Status.CONFIRMED
        appointment.save(update_fields=["status", "updated_at"])
    return current
