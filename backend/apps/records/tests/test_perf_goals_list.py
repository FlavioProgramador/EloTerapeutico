import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.records.treatment_models import TreatmentGoal
from apps.users.models import User


@pytest.fixture
def therapist(db):
    return User.objects.create_user(
        email="therapist_goals_perf@example.com",
        password="safe-password",
        full_name="Terapeuta Metas Perf",
        role=User.Role.THERAPIST,
    )


@pytest.fixture
def patient(therapist):
    return Patient.objects.create(
        full_name="Paciente de Teste Metas",
        therapist=therapist,
        status=Patient.Status.ACTIVE,
    )


@pytest.fixture
def client(therapist):
    api_client = APIClient()
    api_client.force_authenticate(therapist)
    return api_client


def create_goals(therapist, patient, count):
    for i in range(count):
        TreatmentGoal.objects.create(
            patient=patient,
            title=f"Meta {i}",
            status=TreatmentGoal.Status.ACTIVE,
            created_by=therapist,
        )


@pytest.mark.django_db
def test_goals_list_queries_optimized(client, therapist, patient):
    url = reverse("treatment-goals", kwargs={"patient_id": patient.id})

    # Warm up to avoid initial auth/session/content-type queries
    client.get(url)

    # 1. Setup 2 goals
    create_goals(therapist, patient, 2)

    with CaptureQueriesContext(connection) as queries_small:
        response = client.get(url)
        assert response.status_code == 200
        count_small = len(queries_small)

    # Clean up before creating larger dataset
    TreatmentGoal.objects.all().delete()

    # 2. Setup 5 goals
    create_goals(therapist, patient, 5)

    with CaptureQueriesContext(connection) as queries_large:
        response = client.get(url)
        assert response.status_code == 200
        count_large = len(queries_large)

    print("\nGoals List Queries:")
    print(f"Goals (2 items): {count_small}")
    print(f"Goals (5 items): {count_large}")

    # Prior to optimization:
    # - Treatment goals would execute N+1 queries to retrieve creator name (created_by.full_name)
    # After adding select_related, the query count must be constant (equal for small & large datasets).
    assert count_large == count_small
