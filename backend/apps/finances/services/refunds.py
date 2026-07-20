"""Estornos transacionais de lançamentos financeiros."""

from django.db import transaction

from apps.finances.exceptions import InvalidPaymentTransitionError
from apps.finances.models import FinancialTransaction


@transaction.atomic
def refund_transaction(*, financial_transaction):
    current = FinancialTransaction.objects.select_for_update().get(
        pk=financial_transaction.pk
    )
    if not current.can_refund():
        raise InvalidPaymentTransitionError(
            "Apenas transações pagas podem ser estornadas."
        )
    current.payment_status = FinancialTransaction.PaymentStatus.REFUNDED
    current.save(update_fields=["payment_status", "updated_at"])
    return current


reverse_payment = refund_transaction

__all__ = ["refund_transaction", "reverse_payment"]
