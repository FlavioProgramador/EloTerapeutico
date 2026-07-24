import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.records.extended_models import AnamnesisProfile, AnamnesisVersion
from apps.records.models import Anamnesis
from apps.users.models import User


@pytest.fixture
def therapist(db):
    return User.objects.create_user(
        email="therapist_anamnesis_perf@example.com",
        password="safe-password",
        full_name="Terapeuta Anamnese Perf",
        role=User.Role.THERAPIST,
    )


@pytest.fixture
def patient(therapist):
    return Patient.objects.create(
        full_name="Paciente de Teste Anamnese",
        therapist=therapist,
        status=Patient.Status.ACTIVE,
    )


@pytest.fixture
def client(therapist):
    api_client = APIClient()
    api_client.force_authenticate(therapist)
    return api_client


@pytest.mark.django_db
def test_anamnesis_queries_optimized(client, therapist, patient):
    url = f"/api/v1/records/patients/{patient.id}/clinical-anamnesis/"

    # Warm up to avoid initial session/auth queries
    client.get(url)

    # 1. Setup anamnesis, profile, and some versions
    anamnesis = Anamnesis.objects.create(
        patient=patient,
        chief_complaint="Queixa principal de teste",
        created_by=therapist,
    )
    profile = AnamnesisProfile.objects.create(
        anamnesis=anamnesis,
        reason_for_care="Motivo do cuidado",
        updated_by=therapist,
    )
    AnamnesisVersion.objects.create(
        anamnesis=anamnesis,
        version=1,
        snapshot="{}",
        created_by=therapist,
    )

    # Capture queries for a single anamnesis retrieval
    with CaptureQueriesContext(connection) as queries_single:
        response = client.get(url)
        assert response.status_code == 200
        assert response.data["exists"] is True
        assert response.data["version_count"] == 1
        assert response.data["updated_by_name"] == "Terapeuta Anamnese Perf"

    # Make sure we do not have redundant or lazy-loaded queries
    # Queries are:
    # 1. Select patient (access control)
    # 2. Select tenant/membership check
    # 3. Select Anamnesis with select_related("profile", "profile__updated_by") and count annotate.
    # 4. Select Organization
    # 5. Select content type for audit log
    # 6. Insert into users_auditlog
    print(f"\nTotal queries captured: {len(queries_single)}")
    for q in queries_single:
        print(f"QUERY: {q['sql']}\n")

    assert len(queries_single) <= 6
