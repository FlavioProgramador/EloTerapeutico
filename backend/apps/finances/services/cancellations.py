"""Cancelamentos transacionais de lançamentos financeiros."""

from django.db import transaction

from apps.finances.exceptions import InvalidPaymentTransitionError
from apps.finances.models import FinancialTransaction


@transaction.atomic
def cancel_transaction(*, financial_transaction):
    current = FinancialTransaction.objects.select_for_update().get(
        pk=financial_transaction.pk
    )
    if not current.can_cancel():
        raise InvalidPaymentTransitionError(
            "Apenas transações pendentes podem ser canceladas."
        )
    current.payment_status = FinancialTransaction.PaymentStatus.CANCELLED
    current.save(update_fields=["payment_status", "updated_at"])
    return current
