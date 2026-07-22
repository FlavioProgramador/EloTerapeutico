import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.records.extended_models import AnamnesisVersion
from apps.records.models import Evolution
from apps.users.models import User


@pytest.fixture
def therapist(db):
    return User.objects.create_user(
        email="therapist@example.com",
        password="safe-password",
        full_name="Terapeuta Responsável",
        role=User.Role.THERAPIST,
    )


@pytest.fixture
def patient(therapist):
    return Patient.objects.create(
        full_name="Paciente de Teste",
        cpf="52998224725",
        birth_date=timezone.localdate().replace(year=1995),
        therapist=therapist,
        status=Patient.Status.ACTIVE,
    )


@pytest.fixture
def client(therapist):
    api_client = APIClient()
    api_client.force_authenticate(therapist)
    return api_client


@pytest.mark.django_db
def test_outro_terapeuta_nao_acessa_workspace(patient):
    other = User.objects.create_user(
        email="other@example.com",
        password="safe-password",
        full_name="Outro Terapeuta",
        role=User.Role.THERAPIST,
    )
    api_client = APIClient()
    api_client.force_authenticate(other)

    response = api_client.get(f"/api/v1/records/patients/{patient.id}/workspace/")

    # Deve retornar 404 Not Found para evitar vazamento de existência (IDOR / side-channel)
    assert response.status_code == 404


@pytest.mark.django_db
def test_cria_e_finaliza_evolucao(client, patient):
    created = client.post(
        f"/api/v1/records/patients/{patient.id}/clinical-evolutions/",
        {
            "session_date": timezone.localdate().isoformat(),
            "modality": "online",
            "therapist_observations": "Registro de teste.",
        },
        format="json",
    )
    assert created.status_code == 201
    assert created.data["status"] == "draft"
    assert created.data["attached_documents_count"] == 0
    assert created.data["linked_goal_ids"] == []

    finalized = client.post(
        f"/api/v1/records/clinical-evolutions/{created.data['id']}/finalize/",
        {},
        format="json",
    )

    assert finalized.status_code == 200
    assert finalized.data["status"] == "finalized"
    assert Evolution.objects.get(pk=created.data["id"]).is_locked is True


@pytest.mark.django_db
def test_anamnese_cria_versao_antes_da_edicao(client, patient, therapist):
    first = client.patch(
        f"/api/v1/records/patients/{patient.id}/clinical-anamnesis/",
        {"chief_complaint": "Primeira versão"},
        format="json",
    )
    assert first.status_code == 200
    assert first.data["status"] == "draft"
    assert first.data["status_display"] == "Rascunho"
    assert first.data["updated_by_name"] == therapist.full_name

    second = client.patch(
        f"/api/v1/records/patients/{patient.id}/clinical-anamnesis/",
        {"chief_complaint": "Segunda versão"},
        format="json",
    )

    assert second.status_code == 200
    assert AnamnesisVersion.objects.filter(anamnesis__patient=patient).count() == 1
