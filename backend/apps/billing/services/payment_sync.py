from apps.billing.selectors.payments import get_payment_for_refresh
from apps.billing.services.orders import get_gateway, upsert_gateway_payment


class PaymentRefreshUnavailable(Exception):
    """A cobrança não existe no tenant ou não pode ser sincronizada."""


def refresh_gateway_payment(*, user, payment_id: int, gateway=None):
    payment = get_payment_for_refresh(user=user, payment_id=payment_id)
    if not payment or not payment.billing_order or not payment.gateway_payment_id:
        raise PaymentRefreshUnavailable

    gateway = gateway or get_gateway()
    payload = gateway.get_payment(payment.gateway_payment_id)
    return upsert_gateway_payment(
        order=payment.billing_order,
        payload=payload,
        subscription=payment.subscription,
        installment_count=payment.installment_count,
    )
