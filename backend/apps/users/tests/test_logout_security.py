"""Testes de segurança específicos do fluxo de logout."""

import pytest
from django.urls import reverse
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from apps.users.models import AuthSession, User
from apps.users.services.sessions import issue_token_pair


@pytest.mark.django_db
def test_logout_rejects_invalid_refresh_token(api_client):
    response = api_client.post(
        reverse("auth-logout"),
        {"refresh": "token-invalido"},
        format="json",
    )

    assert response.status_code == 400
    assert response.data == {
        "error": {
            "code": "BAD_REQUEST",
            "message": "Token inválido ou já expirado.",
        }
    }


@pytest.mark.django_db
def test_logout_revokes_refresh_and_session_without_access_token(api_client):
    user = User.objects.create_user(
        email="logout-valid@teste.com",
        full_name="Logout Valid",
        password="".join(["Test", "Pass", "2026!", "_valid"]),
    )
    tokens = issue_token_pair(user=user)
    session = AuthSession.objects.get(user=user)

    response = api_client.post(
        reverse("auth-logout"),
        {"refresh": tokens["refresh"]},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["message"] == "Logout realizado com sucesso."
    session.refresh_from_db()
    assert session.revoked_at is not None
    assert session.revoked_reason == "logout"
    assert BlacklistedToken.objects.filter(token__jti=session.refresh_jti).exists()


@pytest.mark.django_db
def test_logout_is_idempotent_for_missing_local_cookie(api_client):
    response = api_client.post(reverse("auth-logout"), {}, format="json")

    assert response.status_code == 400
    assert response.data["error"]["code"] == "BAD_REQUEST"
