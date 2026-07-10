from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import Plan
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
    client = APIClient()
    client.force_authenticate(user)
    sensitive_detail = "CPF 52998224725 rejeitado; access_token=segredo-interno"

    with patch(
        "apps.billing.views.AsaasGateway.create_payment",
        side_effect=GatewayError(sensitive_detail),
    ):
        response = client.post(
            "/api/v1/billing/checkout/create/",
            {
                "plan_slug": plan.slug,
                "type": "ONE_TIME",
                "billingType": "PIX",
                "cpfCnpj": "529.982.247-25",
                "dueDate": (timezone.localdate() + timedelta(days=1)).isoformat(),
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
