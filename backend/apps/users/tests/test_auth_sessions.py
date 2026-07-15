"""Testes de emissão, rotação e revogação das sessões autenticadas."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.users.models import AuthSession, User
from apps.users.services.sessions import SESSION_CLAIM, issue_token_pair

pytestmark = pytest.mark.django_db


def _password(label: str) -> str:
    return "".join(["Test", "Pass", "2026!", "_", label])


def _create_user(label: str) -> User:
    return User.objects.create_user(
        email=f"session-{label}@example.test",
        full_name=f"Sessão {label}",
        password=_password(label),
    )


def test_login_creates_revocable_session_and_embeds_session_claim(api_client):
    user = _create_user("login")

    response = api_client.post(
        reverse("auth-login"),
        {"email": user.email, "password": _password("login")},
        format="json",
    )

    assert response.status_code == 200
    refresh = RefreshToken(response.data["refresh"])
    access = AccessToken(response.data["access"])
    session = AuthSession.objects.get(user=user)
    assert str(refresh[SESSION_CLAIM]) == str(session.public_id)
    assert str(access[SESSION_CLAIM]) == str(session.public_id)
    assert session.refresh_jti == str(refresh["jti"])
    assert session.is_active is True


def test_refresh_rotates_under_same_session_and_rejects_replay(api_client):
    user = _create_user("refresh")
    tokens = issue_token_pair(user=user)
    original_refresh = RefreshToken(tokens["refresh"])
    session_id = str(original_refresh[SESSION_CLAIM])

    first = api_client.post(
        reverse("token-refresh"),
        {"refresh": tokens["refresh"]},
        format="json",
    )

    assert first.status_code == 200
    rotated_refresh = RefreshToken(first.data["refresh"])
    assert str(rotated_refresh[SESSION_CLAIM]) == session_id
    session = AuthSession.objects.get(public_id=session_id)
    assert session.refresh_jti == str(rotated_refresh["jti"])
    assert BlacklistedToken.objects.filter(token__jti=original_refresh["jti"]).exists()

    replay = api_client.post(
        reverse("token-refresh"),
        {"refresh": tokens["refresh"]},
        format="json",
    )
    assert replay.status_code == 401


def test_active_sessions_endpoint_marks_current_session(api_client):
    user = _create_user("current")
    tokens = issue_token_pair(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    response = api_client.get(reverse("auth-session-list"))

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["is_current"] is True
    assert "refresh_jti" not in response.data[0]


def test_user_cannot_revoke_session_owned_by_another_user(api_client):
    owner = _create_user("owner")
    attacker = _create_user("attacker")
    owner_tokens = issue_token_pair(user=owner)
    attacker_tokens = issue_token_pair(user=attacker)
    owner_session = AuthSession.objects.get(user=owner)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {attacker_tokens['access']}")

    response = api_client.post(
        reverse("auth-session-revoke", kwargs={"public_id": owner_session.public_id}),
        {},
        format="json",
    )

    assert response.status_code == 404
    owner_session.refresh_from_db()
    assert owner_session.revoked_at is None
    assert RefreshToken(owner_tokens["refresh"])[SESSION_CLAIM] == str(owner_session.public_id)


def test_logout_revokes_current_session_and_blacklists_refresh(api_client):
    user = _create_user("logout")
    tokens = issue_token_pair(user=user)
    refresh = RefreshToken(tokens["refresh"])
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    response = api_client.post(
        reverse("auth-logout"),
        {"refresh": tokens["refresh"]},
        format="json",
    )

    assert response.status_code == 200
    session = AuthSession.objects.get(user=user)
    assert session.revoked_at is not None
    assert session.revoked_reason == "logout"
    assert BlacklistedToken.objects.filter(token__jti=refresh["jti"]).exists()


def test_logout_all_revokes_every_active_session(api_client):
    user = _create_user("all")
    first = issue_token_pair(user=user)
    second = issue_token_pair(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {first['access']}")

    response = api_client.post(reverse("auth-logout-all"), {}, format="json")

    assert response.status_code == 200
    assert response.data["revoked_sessions"] == 2
    assert not AuthSession.objects.filter(user=user, revoked_at__isnull=True).exists()
    assert BlacklistedToken.objects.filter(token__jti=RefreshToken(first["refresh"])["jti"]).exists()
    assert BlacklistedToken.objects.filter(token__jti=RefreshToken(second["refresh"])["jti"]).exists()


def test_password_change_revokes_all_sessions(api_client):
    user = _create_user("password")
    tokens = issue_token_pair(user=user)
    issue_token_pair(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    response = api_client.post(
        reverse("auth-change-password"),
        {
            "current_password": _password("password"),
            "new_password": _password("password-new"),
            "new_password_confirm": _password("password-new"),
        },
        format="json",
    )

    assert response.status_code == 200
    assert AuthSession.objects.filter(user=user, revoked_at__isnull=True).count() == 0


def test_registration_issues_session_bound_tokens(api_client):
    response = api_client.post(
        reverse("auth-register"),
        {
            "email": "session-register@example.test",
            "full_name": "Cadastro Sessão",
            "phone": "",
            "password": _password("register"),
            "password_confirm": _password("register"),
            "crp": "",
            "specialty": "",
            "terms_accepted": True,
            "privacy_accepted": True,
            "access_mode": "TRIAL",
        },
        format="json",
    )

    assert response.status_code == 201
    user = User.objects.get(email="session-register@example.test")
    session = AuthSession.objects.get(user=user)
    refresh = RefreshToken(response.data["tokens"]["refresh"])
    assert str(refresh[SESSION_CLAIM]) == str(session.public_id)
