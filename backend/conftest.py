"""
conftest.py – Fixtures globais para todos os testes do backend.
"""

import pytest
from rest_framework.test import APIClient

from apps.users.models import User


@pytest.fixture
def api_client():
    """APIClient não autenticado."""
    return APIClient()


@pytest.fixture
def therapist_user(db):
    """Usuário terapeuta para uso nos testes."""
    return User.objects.create_user(
        email="terapeuta@teste.com",
        full_name="Dr. Terapeuta Teste",
        password="senha_segura_123",
        role=User.Role.THERAPIST,
        crp_number="06/123456",
    )


@pytest.fixture
def secretary_user(db):
    """Usuário secretária para testes de permissão."""
    return User.objects.create_user(
        email="secretaria@teste.com",
        full_name="Secretária Teste",
        password="senha_segura_123",
        role=User.Role.SECRETARY,
    )


@pytest.fixture
def admin_user(db):
    """Usuário administrador para testes de permissão."""
    return User.objects.create_user(
        email="admin@teste.com",
        full_name="Admin Teste",
        password="senha_segura_123",
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
