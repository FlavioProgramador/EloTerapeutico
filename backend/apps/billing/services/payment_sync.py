from apps.billing.selectors.payments import get_payment_for_refresh
from apps.billing.services.orders import get_gateway, upsert_gateway_payment


class PaymentRefreshUnavailable(Exception):
    """A cobrança não existe no tenant ou não pode ser sincronizada."""


def refresh_gateway_payment(*, user, payment_id: int, gateway=None):
    """Sincroniza uma cobrança do usuário com o gateway configurado.

    A cobrança é carregada por um selector que aplica o escopo do usuário.
    Após validar os vínculos locais e o identificador externo, o serviço busca
    o estado atual no gateway e delega a persistência ao fluxo de upsert.

    Args:
        user: Usuário autenticado que delimita o escopo da consulta.
        payment_id: Identificador interno da cobrança a ser atualizada.
        gateway: Cliente opcional do gateway, usado para injeção em testes ou
            para substituir a implementação configurada.

    Returns:
        Cobrança local criada ou atualizada a partir do payload do gateway.

    Raises:
        PaymentRefreshUnavailable: Quando a cobrança não pertence ao usuário,
            não existe ou não possui ordem e identificador externo válidos.

    Side Effects:
        Realiza uma chamada ao gateway de pagamentos e persiste o estado
        retornado por meio de ``upsert_gateway_payment``.
    """
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
