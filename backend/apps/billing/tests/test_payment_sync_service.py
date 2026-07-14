from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from apps.billing.services.payment_sync import (
    PaymentRefreshUnavailable,
    refresh_gateway_payment,
)


def test_refresh_gateway_payment_orchestrates_selector_gateway_and_upsert():
    user = SimpleNamespace(pk=9)
    order = object()
    subscription = object()
    payment = SimpleNamespace(
        billing_order=order,
        subscription=subscription,
        gateway_payment_id="pay_123",
        installment_count=3,
    )
    gateway = Mock()
    gateway.get_payment.return_value = {"id": "pay_123", "status": "CONFIRMED"}
    updated_payment = object()

    with (
        patch(
            "apps.billing.services.payment_sync.get_payment_for_refresh",
            return_value=payment,
        ) as selector,
        patch(
            "apps.billing.services.payment_sync.upsert_gateway_payment",
            return_value=updated_payment,
        ) as upsert,
    ):
        result = refresh_gateway_payment(user=user, payment_id=21, gateway=gateway)

    selector.assert_called_once_with(user=user, payment_id=21)
    gateway.get_payment.assert_called_once_with("pay_123")
    upsert.assert_called_once_with(
        order=order,
        payload={"id": "pay_123", "status": "CONFIRMED"},
        subscription=subscription,
        installment_count=3,
    )
    assert result is updated_payment


def test_refresh_gateway_payment_rejects_cross_tenant_or_unsynchronizable_payment():
    with patch(
        "apps.billing.services.payment_sync.get_payment_for_refresh",
        return_value=None,
    ):
        with pytest.raises(PaymentRefreshUnavailable):
            refresh_gateway_payment(user=SimpleNamespace(pk=9), payment_id=21, gateway=Mock())
