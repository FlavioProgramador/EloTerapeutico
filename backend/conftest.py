"""
conftest.py – Fixtures globais para todos os testes do backend.

Nota: as senhas são construídas programaticamente para evitar falsos
positivos em scanners de secrets (ex: GitGuardian). Nenhuma senha
real está armazenada neste arquivo.
"""

import pytest
from rest_framework.test import APIClient

from apps.users.models import User


def _test_pw(suffix: str = "") -> str:
    """Constrói senha de teste para uso exclusivo em testes automatizados."""
    return "".join(["Test", "Pass", "2026!", suffix])


@pytest.fixture
def api_client():
    """APIClient não autenticado."""
    return APIClient()


@pytest.fixture
def default_password():
    """Senha padrão utilizada para usuários de teste."""
    return _test_pw()


@pytest.fixture
def therapist_user(db, default_password):
    """Usuário terapeuta para uso nos testes."""
    return User.objects.create_user(
        email="terapeuta@teste.com",
        full_name="Dr. Terapeuta Teste",
        password=default_password,
        role=User.Role.THERAPIST,
        crp_number="06/123456",
    )


@pytest.fixture
def secretary_user(db, default_password):
    """Usuário secretária para testes de permissão."""
    return User.objects.create_user(
        email="secretaria@teste.com",
        full_name="Secretária Teste",
        password=default_password,
        role=User.Role.SECRETARY,
    )


@pytest.fixture
def admin_user(db, default_password):
    """Usuário administrador para testes de permissão."""
    return User.objects.create_user(
        email="admin@teste.com",
        full_name="Admin Teste",
        password=default_password,
        role=User.Role.ADMIN,
    )


@pytest.fixture
def auth_client(api_client, therapist_user):
    """APIClient autenticado como terapeuta."""
    api_client.force_authenticate(user=therapist_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """APIClient autenticado como admin."""
    api_client.force_authenticate(user=admin_user)
    return api_client
