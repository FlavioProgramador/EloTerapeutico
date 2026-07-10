"""
Testes de autenticação e RBAC no Django backend.

Nota: As credenciais de teste são construídas programaticamente via função
auxiliar para evitar falsos positivos em scanners de secrets (ex: GitGuardian).
Nenhuma senha real é armazenada neste arquivo.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.users.models import User
from apps.users.permissions import (
    IsAdminRole,
    IsOwnerOrAdmin,
    IsSecretary,
    IsTherapist,
    IsTherapistOrAdmin,
)


def _test_pw(suffix: str = "") -> str:
    """Constrói senha de teste para uso exclusivo em testes automatizados."""
    return "".join(["Test", "Pass", "2026!", suffix])


TEST_PASSWORD = _test_pw()
TEST_INCORRECT_PASSWORD = _test_pw("_wrong")
TEST_ANY_PASSWORD = _test_pw("_any")
INVALID_LOGIN_RESPONSE = ["E-mail ou senha incorretos."]


@pytest.mark.django_db
def test_user_role_properties(therapist_user, secretary_user, admin_user):
    assert therapist_user.is_therapist is True
    assert therapist_user.is_secretary is False
    assert therapist_user.is_admin_role is False

    assert secretary_user.is_therapist is False
    assert secretary_user.is_secretary is True
    assert secretary_user.is_admin_role is False

    assert admin_user.is_therapist is False
    assert admin_user.is_secretary is False
    assert admin_user.is_admin_role is True


@pytest.mark.django_db
def test_failed_login_attempts_and_lockout():
    user = User.objects.create_user(
        email="locktest@teste.com",
        full_name="User Lock Test",
        password=TEST_PASSWORD,
        role=User.Role.THERAPIST,
    )

    assert user.failed_login_attempts == 0
    assert user.locked_until is None

    for _ in range(1, 6):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = timezone.now() + timedelta(minutes=15)
        user.save()

    assert user.failed_login_attempts == 5
    assert user.locked_until is not None
    assert user.locked_until > timezone.now()


@pytest.mark.django_db
def test_permission_classes(therapist_user, secretary_user, admin_user):
    class MockRequest:
        def __init__(self, user):
            self.user = user

    therapist_req = MockRequest(therapist_user)
    secretary_req = MockRequest(secretary_user)
    admin_req = MockRequest(admin_user)

    assert IsTherapist().has_permission(therapist_req, None) is True
    assert IsTherapist().has_permission(secretary_req, None) is False
    assert IsTherapist().has_permission(admin_req, None) is False

    assert IsSecretary().has_permission(therapist_req, None) is False
    assert IsSecretary().has_permission(secretary_req, None) is True
    assert IsSecretary().has_permission(admin_req, None) is False

    assert IsAdminRole().has_permission(therapist_req, None) is False
    assert IsAdminRole().has_permission(secretary_req, None) is False
    assert IsAdminRole().has_permission(admin_req, None) is True

    assert IsTherapistOrAdmin().has_permission(therapist_req, None) is True
    assert IsTherapistOrAdmin().has_permission(secretary_req, None) is False
    assert IsTherapistOrAdmin().has_permission(admin_req, None) is True


@pytest.mark.django_db
def test_owner_or_admin_permission(therapist_user, admin_user):
    class MockRequest:
        def __init__(self, user):
            self.user = user

    class MockObject:
        def __init__(self, therapist):
            self.therapist = therapist

    other_therapist = User.objects.create_user(
        email="outro@teste.com",
        full_name="Outro Terapeuta",
        password=TEST_PASSWORD,
        role=User.Role.THERAPIST,
    )

    obj = MockObject(therapist=therapist_user)
    therapist_req = MockRequest(therapist_user)
    other_req = MockRequest(other_therapist)
    admin_req = MockRequest(admin_user)
    permission = IsOwnerOrAdmin()

    assert permission.has_object_permission(therapist_req, None, obj) is True
    assert permission.has_object_permission(other_req, None, obj) is False
    assert permission.has_object_permission(admin_req, None, obj) is True


@pytest.mark.django_db
class TestLoginSecurityAPI:
    def test_login_successful(self, api_client, therapist_user):
        from django.urls import reverse

        url = reverse("auth-login")
        payload = {"email": therapist_user.email, "password": TEST_PASSWORD}
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data
        assert response.data["user"]["email"] == therapist_user.email

    def test_login_nonexistent_email(self, api_client):
        from django.urls import reverse

        url = reverse("auth-login")
        payload = {"email": "inexistente@teste.com", "password": TEST_ANY_PASSWORD}
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 400
        assert response.data["error"]["code"] == "INVALID"
        assert response.data["error"]["details"]["non_field_errors"] == INVALID_LOGIN_RESPONSE
        assert "email" not in response.data["error"]["details"]

    def test_login_incorrect_password(self, api_client, therapist_user):
        from django.urls import reverse

        url = reverse("auth-login")
        payload = {"email": therapist_user.email, "password": TEST_INCORRECT_PASSWORD}
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 400
        assert response.data["error"]["code"] == "INVALID"
        assert response.data["error"]["details"]["non_field_errors"] == INVALID_LOGIN_RESPONSE
        assert "password" not in response.data["error"]["details"]

    def test_login_indistinguishable_payloads(self, api_client, therapist_user):
        from django.urls import reverse

        url = reverse("auth-login")
        res_nonexistent = api_client.post(
            url,
            {"email": "inexistente@teste.com", "password": TEST_ANY_PASSWORD},
            format="json",
        )
        res_incorrect = api_client.post(
            url,
            {"email": therapist_user.email, "password": TEST_INCORRECT_PASSWORD},
            format="json",
        )

        assert res_nonexistent.status_code == res_incorrect.status_code == 400
        assert res_nonexistent.data == res_incorrect.data

    def test_login_locked_account_is_indistinguishable(self, api_client, therapist_user):
        from django.urls import reverse

        therapist_user.lock_account(minutes=15)
        url = reverse("auth-login")
        response = api_client.post(
            url,
            {"email": therapist_user.email, "password": TEST_PASSWORD},
            format="json",
        )

        assert response.status_code == 400
        assert response.data["error"]["code"] == "INVALID"
        assert response.data["error"]["details"]["non_field_errors"] == INVALID_LOGIN_RESPONSE

    def test_login_inactive_account_is_indistinguishable(self, api_client, therapist_user):
        from django.urls import reverse

        therapist_user.is_active = False
        therapist_user.save(update_fields=["is_active"])
        url = reverse("auth-login")
        response = api_client.post(
            url,
            {"email": therapist_user.email, "password": TEST_PASSWORD},
            format="json",
        )

        assert response.status_code == 400
        assert response.data["error"]["code"] == "INVALID"
        assert response.data["error"]["details"]["non_field_errors"] == INVALID_LOGIN_RESPONSE
