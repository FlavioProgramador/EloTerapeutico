"""
conftest.py – Fixtures globais para todos os testes do backend.

A compatibilidade multi-tenant abaixo existe somente durante pytest. Ela associa
fixtures legadas a uma organização determinística sem tornar os campos de tenant
opcionais no código de produção.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from django.db.models.signals import pre_save
from rest_framework.test import APIClient

from apps.organizations.models import (
    Organization,
    OrganizationMembership,
    OrganizationSettings,
    ProfessionalProfile,
)
from apps.users.models import User

TEST_ORGANIZATION_SLUG = "pytest-default-organization"


def _test_pw(suffix: str = "") -> str:
    """Constrói senha de teste para uso exclusivo em testes automatizados."""

    return "".join(["Test", "Pass", "2026!", suffix])


def _membership_role_for_user(user: User) -> str:
    if user.role == User.Role.ADMIN:
        return OrganizationMembership.Role.ADMIN
    if user.role == User.Role.SECRETARY:
        return OrganizationMembership.Role.RECEPTIONIST
    return OrganizationMembership.Role.THERAPIST


def _ensure_test_organization(user: User) -> Organization:
    """Cria o tenant padrão somente quando uma fixture legada realmente o exige."""

    organization = Organization.objects.filter(slug=TEST_ORGANIZATION_SLUG).first()
    if organization is None:
        organization = Organization.objects.create(
            name="Organização padrão dos testes",
            slug=TEST_ORGANIZATION_SLUG,
            organization_type=Organization.Type.CLINIC,
            status=Organization.Status.ACTIVE,
            created_by=user,
        )
        OrganizationSettings.objects.create(
            organization=organization,
            business_name_on_documents=organization.name,
        )

    membership, _ = OrganizationMembership.objects.get_or_create(
        organization=organization,
        user=user,
        defaults={
            "role": _membership_role_for_user(user),
            "status": OrganizationMembership.Status.ACTIVE,
            "is_default": not OrganizationMembership.objects.filter(
                user=user,
                is_default=True,
            ).exists(),
        },
    )
    if membership.status != OrganizationMembership.Status.ACTIVE:
        membership.status = OrganizationMembership.Status.ACTIVE
        membership.save(update_fields=["status", "updated_at"])
    if membership.role in {
        OrganizationMembership.Role.OWNER,
        OrganizationMembership.Role.ADMIN,
        OrganizationMembership.Role.THERAPIST,
    }:
        ProfessionalProfile.objects.get_or_create(
            membership=membership,
            defaults={
                "display_name": user.display_name or user.full_name,
                "public_email": user.email,
            },
        )
    return organization


def _derive_organization(instance):
    for relation_name in ("patient", "appointment", "package", "membership"):
        relation_id = getattr(instance, f"{relation_name}_id", None)
        if not relation_id:
            continue
        relation = getattr(instance, relation_name, None)
        organization = getattr(relation, "organization", None)
        if organization is not None:
            return organization

    for user_field in ("therapist", "owner", "user", "created_by", "uploaded_by"):
        user_id = getattr(instance, f"{user_field}_id", None)
        if not user_id:
            continue
        user = getattr(instance, user_field, None)
        if user is not None:
            return _ensure_test_organization(user)
    return None


def _assign_legacy_test_tenant(sender, instance, raw=False, **kwargs):
    if raw or sender in {
        Organization,
        OrganizationMembership,
        OrganizationSettings,
        ProfessionalProfile,
    }:
        return
    field_names = {field.name for field in sender._meta.get_fields()}
    if "organization" not in field_names or getattr(instance, "organization_id", None):
        return
    organization = _derive_organization(instance)
    if organization is not None:
        instance.organization = organization


pre_save.connect(
    _assign_legacy_test_tenant,
    weak=False,
    dispatch_uid=f"pytest-model-tenant-{uuid4()}",
)


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
    api_client.credentials(
        HTTP_X_ORGANIZATION_ID=str(_ensure_test_organization(therapist_user).pk)
    )
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """APIClient autenticado como admin."""

    api_client.force_authenticate(user=admin_user)
    api_client.credentials(
        HTTP_X_ORGANIZATION_ID=str(_ensure_test_organization(admin_user).pk)
    )
    return api_client
