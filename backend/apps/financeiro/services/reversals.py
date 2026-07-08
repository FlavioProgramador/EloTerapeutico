"""Estorno transacional de lançamentos financeiros."""

from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import FinancialTransaction


@transaction.atomic
def reverse_payment(*, financial_transaction):
    current = FinancialTransaction.objects.select_for_update().get(pk=financial_transaction.pk)
    if not current.can_refund():
        raise ValidationError("Apenas transações pagas podem ser estornadas.")
    current.payment_status = FinancialTransaction.PaymentStatus.REFUNDED
    current.save(update_fields=["payment_status", "updated_at"])
    return current
