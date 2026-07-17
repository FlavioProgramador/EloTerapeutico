import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.records.extended_models import EvolutionVersion
from apps.records.models import ClinicalDocument, Evolution, EvolutionAddendum
from apps.records.models.evolution_clinical_data import EvolutionClinicalData
from apps.users.models import User


@pytest.fixture
def therapist(db):
    return User.objects.create_user(
        email="therapist_perf@example.com",
        password="safe-password",
        full_name="Terapeuta Perf",
        role=User.Role.THERAPIST,
    )

@pytest.fixture
def patient(therapist):
    return Patient.objects.create(
        full_name="Paciente de Teste",
        therapist=therapist,
        status=Patient.Status.ACTIVE,
    )

@pytest.fixture
def client(therapist):
    api_client = APIClient()
    api_client.force_authenticate(therapist)
    return api_client

def create_evolutions(therapist, patient, count):
    for i in range(count):
        evo = Evolution.objects.create(
            patient=patient,
            session_date=timezone.localdate(),
            created_by=therapist,
            content=f"Sessão {i}"
        )
        EvolutionClinicalData.objects.create(evolution=evo, updated_by=therapist)
        EvolutionVersion.objects.create(evolution=evo, version=1, snapshot="{}", created_by=therapist)
        EvolutionAddendum.objects.create(evolution=evo, reason="Test", content="Test", created_by=therapist)
        ClinicalDocument.objects.create(
            patient=patient,
            evolution=evo,
            original_name=f"doc{i}.pdf",
            size_bytes=100,
            checksum=f"hash{i}",
            uploaded_by=therapist
        )

@pytest.mark.django_db
def test_evolution_list_queries_optimized(client, therapist, patient):
    # Warm up to avoid initial auth queries
    client.get(f"/api/v1/records/patients/{patient.id}/clinical-evolutions/")

    # Setup 2 evolutions
    create_evolutions(therapist, patient, 2)

    print("\n--- Queries with 2 evolutions ---")
    with CaptureQueriesContext(connection) as queries_small:
        response = client.get(f"/api/v1/records/patients/{patient.id}/clinical-evolutions/")
        assert response.status_code == 200
        count_small = len(queries_small)

    # Setup 3 more evolutions (total 5)
    create_evolutions(therapist, patient, 3)

    print("\n--- Queries with 5 evolutions ---")
    with CaptureQueriesContext(connection) as queries_large:
        response = client.get(f"/api/v1/records/patients/{patient.id}/clinical-evolutions/")
        assert response.status_code == 200
        count_large = len(queries_large)

    print("\nSummary:")
    print(f"Queries with 2 evolutions: {count_small}")
    print(f"Queries with 5 evolutions: {count_large}")

    # Query count should be independent of number of results
    assert count_large == count_small

    # Check that data is correct
    data = response.data['results']
    assert len(data) == 5
    for item in data:
        assert item['version_count'] == 1
        assert item['addenda_count'] == 1
        assert item['attached_documents_count'] == 1
