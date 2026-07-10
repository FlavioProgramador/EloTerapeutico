"""Testes de segurança específicos do fluxo de logout."""

import pytest
from django.urls import reverse
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User


@pytest.mark.django_db
def test_logout_rejects_refresh_token_from_another_user(api_client):
    user = User.objects.create_user(
        email="logout-owner@teste.com",
        full_name="Logout Owner",
        password="".join(["Test", "Pass", "2026!", "_owner"]),
    )
    other_user = User.objects.create_user(
        email="logout-other@teste.com",
        full_name="Logout Other",
        password="".join(["Test", "Pass", "2026!", "_other"]),
    )
    other_refresh = RefreshToken.for_user(other_user)

    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("auth-logout"),
        {"refresh": str(other_refresh)},
        format="json",
    )

    assert response.status_code == 400
    assert response.data == {
        "error": {
            "code": "BAD_REQUEST",
            "message": "Token inválido ou já expirado.",
        }
    }
    assert not BlacklistedToken.objects.filter(token__jti=other_refresh["jti"]).exists()


@pytest.mark.django_db
def test_logout_blacklists_refresh_token_owned_by_authenticated_user(api_client):
    user = User.objects.create_user(
        email="logout-valid@teste.com",
        full_name="Logout Valid",
        password="".join(["Test", "Pass", "2026!", "_valid"]),
    )
    refresh = RefreshToken.for_user(user)

    api_client.force_authenticate(user=user)
    response = api_client.post(
        reverse("auth-logout"),
        {"refresh": str(refresh)},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["message"] == "Logout realizado com sucesso."
    assert BlacklistedToken.objects.filter(token__jti=refresh["jti"]).exists()
