from decimal import Decimal

import pytest

from apps.finances.exceptions import InvalidPaymentAmountError
from apps.finances.models import FinancialTransaction
from apps.finances.services import register_payment


@pytest.mark.django_db
def test_register_payment_supports_multiple_partial_payments(therapist_user):
    item = FinancialTransaction.objects.create(therapist=therapist_user, amount=Decimal("100.00"))
    item = register_payment(financial_transaction=item, payment_method="pix", amount=Decimal("30.00"))
    assert item.payment_status == FinancialTransaction.PaymentStatus.PARTIAL
    item = register_payment(financial_transaction=item, payment_method="pix", amount=Decimal("70.00"))
    assert item.payment_status == FinancialTransaction.PaymentStatus.PAID
    assert item.outstanding_amount == Decimal("0.00")


@pytest.mark.django_db
def test_register_payment_rejects_amount_greater_than_balance(therapist_user):
    item = FinancialTransaction.objects.create(therapist=therapist_user, amount=Decimal("100.00"))
    with pytest.raises(InvalidPaymentAmountError):
        register_payment(financial_transaction=item, payment_method="pix", amount=Decimal("101.00"))
