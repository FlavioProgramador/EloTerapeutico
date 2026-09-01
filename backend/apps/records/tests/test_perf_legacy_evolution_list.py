import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.records.models import Evolution, EvolutionAddendum
from apps.users.models import User


@pytest.fixture
def therapist(db):
    return User.objects.create_user(
        email="therapist_legacy_perf@example.com",
        password="safe-password",
        full_name="Terapeuta Legacy Perf",
        role=User.Role.THERAPIST,
    )


@pytest.fixture
def patient(therapist):
    return Patient.objects.create(
        full_name="Paciente Legacy Teste",
        therapist=therapist,
        status=Patient.Status.ACTIVE,
    )


@pytest.fixture
def client(therapist):
    api_client = APIClient()
    api_client.force_authenticate(therapist)
    return api_client


def create_legacy_evolutions(therapist, patient, count):
    for i in range(count):
        evo = Evolution.objects.create(
            patient=patient,
            session_date=timezone.localdate(),
            created_by=therapist,
            content=f"Conteudo {i}",
        )
        EvolutionAddendum.objects.create(
            evolution=evo,
            reason="Motivo",
            content="Aditivo",
            created_by=therapist,
        )


@pytest.mark.django_db
def test_legacy_evolution_list_queries_optimized(client, therapist, patient):
    # Warm up authentication / cache
    client.get(f"/api/v1/records/evolutions/?patient={patient.id}")

    create_legacy_evolutions(therapist, patient, 2)

    with CaptureQueriesContext(connection) as queries_small:
        response = client.get(f"/api/v1/records/evolutions/?patient={patient.id}")
        assert response.status_code == 200
        count_small = len(queries_small)

    create_legacy_evolutions(therapist, patient, 3)

    with CaptureQueriesContext(connection) as queries_large:
        response = client.get(f"/api/v1/records/evolutions/?patient={patient.id}")
        assert response.status_code == 200
        count_large = len(queries_large)

    print(f"\nQueries for 2 evolutions: {count_small}")
    print(f"Queries for 5 evolutions: {count_large}")

    assert count_large == count_small

    data = response.data
    results = data["results"] if isinstance(data, dict) and "results" in data else data
    assert len(results) == 5
    for item in results:
        assert item["addenda_count"] == 1
        assert "created_by_name" in item
