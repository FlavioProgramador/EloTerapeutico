import pytest
from django.contrib.auth.models import Permission
from django.utils import timezone
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.records.evolution_flow_models import ClinicalEvolutionTemplate
from apps.records.extended_models import EvolutionClinicalData
from apps.users.models import User


@pytest.fixture
def therapist(db):
    return User.objects.create_user(
        email="security.therapist@example.com",
        password="safe-password",
        full_name="Terapeuta Segurança",
        role=User.Role.THERAPIST,
    )


@pytest.fixture
def patient(therapist):
    return Patient.objects.create(
        full_name="Paciente Segurança",
        therapist=therapist,
        status=Patient.Status.ACTIVE,
    )


@pytest.fixture
def api(therapist):
    client = APIClient()
    client.force_authenticate(therapist)
    return client


def endpoint(patient):
    return f"/api/v1/records/patients/{patient.id}/clinical-evolutions/"


def payload(**overrides):
    data = {
        "session_date": timezone.localdate().isoformat(),
        "content": "Registro clínico protegido.",
        "therapist_observations": "Registro clínico protegido.",
        "is_confidential": False,
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_secretaria_nao_acessa_evolucoes(patient):
    secretary = User.objects.create_user(
        email="secretary.security@example.com",
        password="safe-password",
        full_name="Secretária",
        role=User.Role.SECRETARY,
    )
    client = APIClient()
    client.force_authenticate(secretary)

    assert client.get(endpoint(patient)).status_code == 403


@pytest.mark.django_db
def test_confidencial_exige_permissao_explicita(api, patient):
    created = api.post(
        endpoint(patient),
        payload(is_confidential=True),
        format="json",
    )
    admin = User.objects.create_user(
        email="clinical.admin.security@example.com",
        password="safe-password",
        full_name="Administrador Clínico",
        role=User.Role.ADMIN,
    )
    client = APIClient()
    client.force_authenticate(admin)
    detail = f"/api/v1/records/clinical-evolutions/{created.data['id']}/"

    assert client.get(detail).status_code == 403
    permission = Permission.objects.get(
        codename="view_confidential_evolution",
        content_type__app_label="records",
    )
    admin.user_permissions.add(permission)
    admin = User.objects.get(pk=admin.pk)
    client.force_authenticate(admin)
    assert client.get(detail).status_code == 200


@pytest.mark.django_db
def test_template_privado_e_arquivamento(api, patient, therapist):
    template = api.post(
        "/api/v1/records/clinical-templates/",
        {"name": "Sessão padrão", "content": "**Objetivo**\n\n- Intervenção"},
        format="json",
    )
    created = api.post(endpoint(patient), payload(), format="json")
    archived = api.delete(
        f"/api/v1/records/clinical-evolutions/{created.data['id']}/"
    )

    assert template.status_code == 201
    assert ClinicalEvolutionTemplate.objects.get().owner == therapist
    assert archived.status_code == 204
    assert (
        EvolutionClinicalData.objects.get(evolution_id=created.data["id"]).status
        == EvolutionClinicalData.Status.ARCHIVED
    )
