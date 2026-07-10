from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Plan, PlanPrice
from apps.billing.services.gateways.base import GatewayError
from apps.users.models import User


@pytest.mark.django_db
def test_checkout_nao_expoe_detalhes_internos_do_gateway():
    user = User.objects.create_user(
        email="gateway.error@example.com",
        full_name="Usuário Gateway",
    )
    plan = Plan.objects.create(
        name="Plano Gateway",
        slug="plano-gateway-security",
        price="89.90",
    )
    price = PlanPrice.objects.create(
        plan=plan,
        name="Plano Gateway anual à vista",
        slug="plano-gateway-security-anual",
        total_amount="899.00",
        billing_interval=PlanPrice.BillingInterval.YEARLY,
        billing_model=PlanPrice.BillingModel.ONE_TIME,
    )
    client = APIClient()
    client.force_authenticate(user)
    sensitive_detail = "CPF 52998224725 rejeitado; access_token=segredo-interno"
    gateway = Mock()
    gateway.create_customer.return_value = {"id": "cus_gateway_security"}
    gateway.create_single_payment.side_effect = GatewayError(sensitive_detail)

    with patch("apps.billing.services.orders.get_gateway", return_value=gateway):
        response = client.post(
            "/api/v1/billing/checkout/create/",
            {
                "plan_price_id": price.pk,
                "billingType": "PIX",
                "cpfCnpj": "529.982.247-25",
                "dueDate": (timezone.localdate() + timedelta(days=1)).isoformat(),
                "installmentCount": 1,
                "idempotency_key": "gateway-security-test-001",
            },
            format="json",
        )

    assert response.status_code == 502
    assert sensitive_detail not in str(response.data)
    assert "52998224725" not in str(response.data)
    assert "segredo-interno" not in str(response.data)
    assert response.data["detail"] == (
        "Não foi possível concluir a operação de cobrança. Tente novamente mais tarde."
    )
