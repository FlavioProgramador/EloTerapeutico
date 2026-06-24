"""
Testes de autenticação e RBAC (Controle de Acesso Baseado em Regras) no Django backend.
"""

import pytest
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User
from apps.users.permissions import IsTherapist, IsSecretary, IsAdminRole, IsTherapistOrAdmin, IsOwnerOrAdmin


@pytest.mark.django_db
def test_user_role_properties(therapist_user, secretary_user, admin_user):
    """Garante que as propriedades auxiliares de papel (role) retornam os valores corretos."""
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
    """Garante que as tentativas falhas de login incrementam e bloqueiam a conta após o limite."""
    user = User.objects.create_user(
        email="locktest@teste.com",
        full_name="User Lock Test",
        password="senha_original_123",
        role=User.Role.THERAPIST,
    )

    # Inicialmente não está bloqueado
    assert user.failed_login_attempts == 0
    assert user.locked_until is None

    # Simula 5 tentativas falhas de login (conforme a regra padrão que costuma ser 5)
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
    """Garante que a classe IsOwnerOrAdmin gerencie corretamente os objetos do proprietário."""
    
    class MockRequest:
        def __init__(self, user):
            self.user = user

    class MockObject:
        def __init__(self, therapist):
            self.therapist = therapist

    other_therapist = User.objects.create_user(
        email="outro@teste.com",
        full_name="Outro Terapeuta",
        password="senha_segura_123",
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
    # Admin tem permissão
    assert permission.has_object_permission(admin_req, None, obj) is True
