import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.records.models import Evolution
from apps.records.models.evolution_clinical_data import EvolutionClinicalData
from apps.records.treatment_models import ClinicalDocument, TreatmentGoal
from apps.users.models import User


@pytest.fixture
def therapist(db):
    return User.objects.create_user(
        email="therapist_summary_perf@example.com",
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


def create_summary_data(therapist, patient, count):
    # Setup some goals
    for i in range(count):
        goal = TreatmentGoal.objects.create(
            patient=patient,
            title=f"Meta {i}",
            status=TreatmentGoal.Status.ACTIVE,
            created_by=therapist,
        )

    # Setup some documents with uploaded_by and evolution
    for i in range(count):
        evo = Evolution.objects.create(
            patient=patient,
            session_date=timezone.localdate(),
            created_by=therapist,
            content=f"Sessão {i}"
        )
        EvolutionClinicalData.objects.create(evolution=evo, updated_by=therapist)

        ClinicalDocument.objects.create(
            patient=patient,
            evolution=evo,
            original_name=f"doc_summary_{i}.pdf",
            size_bytes=100,
            checksum=f"hash_summary_{i}",
            uploaded_by=therapist,
            category="assessment",
        )


@pytest.mark.django_db
def test_record_summary_queries_optimized(client, therapist, patient):
    # Warm up to avoid initial auth/session queries
    client.get(f"/api/v1/records/patients/{patient.id}/workspace/")

    # Setup 2 goals and 2 documents
    create_summary_data(therapist, patient, 2)

    with CaptureQueriesContext(connection) as queries_small:
        response = client.get(f"/api/v1/records/patients/{patient.id}/workspace/")
        assert response.status_code == 200
        count_small = len(queries_small)

    # Clean up and setup 4 goals and 4 documents (PatientRecordSummaryView limits to 4 elements)
    ClinicalDocument.objects.all().delete()
    EvolutionClinicalData.objects.all().delete()
    Evolution.objects.all().delete()
    TreatmentGoal.objects.all().delete()

    create_summary_data(therapist, patient, 4)

    with CaptureQueriesContext(connection) as queries_large:
        response = client.get(f"/api/v1/records/patients/{patient.id}/workspace/")
        assert response.status_code == 200
        count_large = len(queries_large)

    print("\nSummary Page Queries:")
    print(f"Queries with 2 items: {count_small}")
    print(f"Queries with 4 items: {count_large}")

    # Prior to optimization, count_large > count_small due to:
    # 1. goals lacking select_related('created_by')
    # 2. documents lacking select_related('evolution', 'uploaded_by')
    # Query count should be identical and independent of the number of items.
    assert count_large == count_small
