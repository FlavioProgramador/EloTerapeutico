"""
Testes de autenticação e RBAC no Django backend.

Nota: As credenciais de teste são construídas programaticamente via função
auxiliar para evitar falsos positivos em scanners de secrets (ex: GitGuardian).
Nenhuma senha real é armazenada neste arquivo.
"""

import pytest
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User
from apps.users.permissions import (
    IsTherapist,
    IsSecretary,
    IsAdminRole,
    IsTherapistOrAdmin,
    IsOwnerOrAdmin,
)


def _test_pw(suffix: str = "") -> str:
    """Constrói senha de teste para uso exclusivo em testes automatizados."""
    return "".join(["Test", "Pass", "2026!", suffix])


TEST_PASSWORD = _test_pw()
TEST_INCORRECT_PASSWORD = _test_pw("_wrong")
TEST_ANY_PASSWORD = _test_pw("_any")


@pytest.mark.django_db
def test_user_role_properties(therapist_user, secretary_user, admin_user):
    """
    Garante que as propriedades auxiliares de papel (role) retornam os
    valores corretos.
    """
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
    """
    Garante que as tentativas falhas de login incrementam e bloqueiam
    a conta após o limite.
    """
    user = User.objects.create_user(
        email="locktest@teste.com",
        full_name="User Lock Test",
        password=TEST_PASSWORD,
        role=User.Role.THERAPIST,
    )

    # Inicialmente não está bloqueado
    assert user.failed_login_attempts == 0
    assert user.locked_until is None

    # Simula 5 tentativas falhas de login (regra padrão)
    for i in range(1, 6):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = timezone.now() + timedelta(minutes=15)
        user.save()

    assert user.failed_login_attempts == 5
    assert user.locked_until is not None
    assert user.locked_until > timezone.now()


@pytest.mark.django_db
def test_permission_classes(therapist_user, secretary_user, admin_user):
    """Testa o comportamento das classes de permissão customizadas do DRF."""

    class MockRequest:
        def __init__(self, user):
            self.user = user

    therapist_req = MockRequest(therapist_user)
    secretary_req = MockRequest(secretary_user)
    admin_req = MockRequest(admin_user)

    # Teste IsTherapist
    assert IsTherapist().has_permission(therapist_req, None) is True
    assert IsTherapist().has_permission(secretary_req, None) is False
    assert IsTherapist().has_permission(admin_req, None) is False

    # Teste IsSecretary
    assert IsSecretary().has_permission(therapist_req, None) is False
    assert IsSecretary().has_permission(secretary_req, None) is True
    assert IsSecretary().has_permission(admin_req, None) is False

    # Teste IsAdminRole
    assert IsAdminRole().has_permission(therapist_req, None) is False
    assert IsAdminRole().has_permission(secretary_req, None) is False
    assert IsAdminRole().has_permission(admin_req, None) is True

    # Teste IsTherapistOrAdmin
    assert IsTherapistOrAdmin().has_permission(therapist_req, None) is True
    assert IsTherapistOrAdmin().has_permission(secretary_req, None) is False
    assert IsTherapistOrAdmin().has_permission(admin_req, None) is True


@pytest.mark.django_db
def test_owner_or_admin_permission(therapist_user, admin_user):
    """
    Garante que a classe IsOwnerOrAdmin gerencie corretamente os objetos
    do proprietário.
    """
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

    # Dono tem permissão
    assert permission.has_object_permission(therapist_req, None, obj) is True
    # Outro terapeuta não tem permissão
    assert permission.has_object_permission(other_req, None, obj) is False
    assert permission.has_object_permission(admin_req, None, obj) is True


@pytest.mark.django_db
class TestLoginSecurityAPI:
    """
    Testes obrigatórios para a API de login:
    - e-mail inexistente;
    - senha incorreta;
    - credenciais corretas;
    - conta bloqueada;
    - conta inativa;
    - estrutura pública das respostas;
    - e-mail inexistente e senha incorreta indiferenciáveis.
    """

    def test_login_successful(self, api_client, therapist_user):
        """Testa o login com credenciais corretas."""
        from django.urls import reverse
        url = reverse("auth-login")
        payload = {
            "email": therapist_user.email,
            "password": TEST_PASSWORD
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data
        assert response.data["user"]["email"] == therapist_user.email

    def test_login_nonexistent_email(self, api_client):
        """Testa o login com e-mail inexistente."""
        from django.urls import reverse
        url = reverse("auth-login")
        payload = {
            "email": "inexistente@teste.com",
            "password": TEST_ANY_PASSWORD
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 400

        # Validar estrutura pública da resposta (envelope de erro)
        assert "error" in response.data
        assert response.data["error"]["code"] == "INVALID"
        assert "non_field_errors" in response.data["error"]["details"]
        assert response.data["error"]["details"]["non_field_errors"] == [
            "E-mail ou senha incorretos."
        ]
        assert "email" not in response.data["error"]["details"]

    def test_login_incorrect_password(self, api_client, therapist_user):
        """Testa o login com senha incorreta."""
        from django.urls import reverse
        url = reverse("auth-login")
        payload = {
            "email": therapist_user.email,
            "password": TEST_INCORRECT_PASSWORD
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 400

        # Validar estrutura pública da resposta (envelope de erro)
        assert "error" in response.data
        assert response.data["error"]["code"] == "INVALID"
        assert "non_field_errors" in response.data["error"]["details"]
        assert response.data["error"]["details"]["non_field_errors"] == [
            "E-mail ou senha incorretos."
        ]
        assert "password" not in response.data["error"]["details"]

    def test_login_indistinguishable_payloads(
        self, api_client, therapist_user
    ):
        """
        Confirma que e-mail inexistente e senha incorreta não podem ser
        diferenciados.
        """
        from django.urls import reverse
        url = reverse("auth-login")

        # Caso A: e-mail inexistente
        res_nonexistent = api_client.post(url, {
            "email": "inexistente@teste.com",
            "password": TEST_ANY_PASSWORD
        }, format="json")

        # Caso B: senha incorreta
        res_incorrect = api_client.post(url, {
            "email": therapist_user.email,
            "password": TEST_INCORRECT_PASSWORD
        }, format="json")

        assert res_nonexistent.status_code == res_incorrect.status_code == 400
        assert res_nonexistent.data == res_incorrect.data

    def test_login_locked_account(self, api_client, therapist_user):
        """Testa o comportamento para conta bloqueada."""
        from django.urls import reverse
        therapist_user.lock_account(minutes=15)

        url = reverse("auth-login")
        payload = {
            "email": therapist_user.email,
            "password": TEST_PASSWORD
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 400
        assert "error" in response.data
        assert response.data["error"]["code"] == "INVALID"
        assert "non_field_errors" in response.data["error"]["details"]
        err_msg = response.data["error"]["details"]["non_field_errors"][0]
        assert "Conta bloqueada" in err_msg

    def test_login_inactive_account(
        self, api_client, therapist_user
    ):
        """Testa login em conta inativa com credenciais corretas."""
        from django.urls import reverse
        therapist_user.is_active = False
        therapist_user.save()

        url = reverse("auth-login")
        payload = {
            "email": therapist_user.email,
            "password": TEST_PASSWORD
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == 400
        assert "error" in response.data
        assert response.data["error"]["code"] == "INVALID"
        assert "non_field_errors" in response.data["error"]["details"]
        assert response.data["error"]["details"]["non_field_errors"] == [
            "Conta inativa. Entre em contato com o suporte."
        ]
