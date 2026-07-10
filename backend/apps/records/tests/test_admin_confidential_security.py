from datetime import date

import pytest
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.test import RequestFactory

from apps.patients.models import Patient
from apps.records.admin_parts.evolution import EvolutionAdmin
from apps.records.models import Evolution
from apps.users.models import User


@pytest.fixture
def admin_context(db):
    therapist = User.objects.create_user(
        email="admin-records.owner@example.com",
        password="password",
        full_name="Autor Clínico",
        role=User.Role.THERAPIST,
    )
    superuser = User.objects.create_superuser(
        email="admin-records.super@example.com",
        password="password",
        full_name="Administrador Global",
    )
    superuser.role = User.Role.ADMIN
    superuser.save(update_fields=["role"])
    patient = Patient.objects.create(
        full_name="Paciente Admin",
        therapist=therapist,
        status=Patient.Status.ACTIVE,
    )
    public_evolution = Evolution.objects.create(
        patient=patient,
        created_by=therapist,
        session_date=date.today(),
        content="Evolução comum",
        is_confidential=False,
    )
    confidential_evolution = Evolution.objects.create(
        patient=patient,
        created_by=therapist,
        session_date=date.today(),
        content="Evolução confidencial",
        is_confidential=True,
    )
    return therapist, superuser, public_evolution, confidential_evolution


@pytest.mark.django_db
def test_superusuario_nao_lista_confidencial_sem_permissao_explicita(admin_context):
    _, superuser, public_evolution, confidential_evolution = admin_context
    request = RequestFactory().get("/admin/records/evolution/")
    request.user = superuser
    model_admin = EvolutionAdmin(Evolution, admin.site)

    returned_ids = set(model_admin.get_queryset(request).values_list("id", flat=True))

    assert public_evolution.id in returned_ids
    assert confidential_evolution.id not in returned_ids


@pytest.mark.django_db
def test_superusuario_lista_confidencial_com_permissao_explicita(admin_context):
    _, superuser, _, confidential_evolution = admin_context
    permission = Permission.objects.get(
        codename="view_confidential_evolution",
        content_type__app_label="records",
    )
    superuser.user_permissions.add(permission)
    superuser.refresh_from_db()
    request = RequestFactory().get("/admin/records/evolution/")
    request.user = superuser
    model_admin = EvolutionAdmin(Evolution, admin.site)

    returned_ids = set(model_admin.get_queryset(request).values_list("id", flat=True))

    assert confidential_evolution.id in returned_ids
