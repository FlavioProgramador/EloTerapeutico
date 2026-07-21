import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.records.treatment_models import ClinicalExport, ClinicalFormResponse
from apps.users.models import User


@pytest.fixture
def therapist(db):
    return User.objects.create_user(
        email="therapist_lists_perf@example.com",
        password="safe-password",
        full_name="Terapeuta Listas Perf",
        role=User.Role.THERAPIST,
    )


@pytest.fixture
def patient(therapist):
    return Patient.objects.create(
        full_name="Paciente de Teste Listas",
        therapist=therapist,
        status=Patient.Status.ACTIVE,
    )


@pytest.fixture
def client(therapist):
    api_client = APIClient()
    api_client.force_authenticate(therapist)
    return api_client


def create_form_responses(therapist, patient, count):
    for i in range(count):
        ClinicalFormResponse.objects.create(
            patient=patient,
            form_name=f"Formulário {i}",
            category="Anamnese",
            therapist=therapist,
        )


def create_clinical_exports(therapist, patient, count):
    for i in range(count):
        ClinicalExport.objects.create(
            patient=patient,
            export_type="Completo",
            filename=f"export_{i}.pdf",
            created_by=therapist,
        )


@pytest.mark.django_db
def test_clinical_lists_queries_optimized(client, therapist, patient):
    form_url = reverse("patient-forms", kwargs={"patient_id": patient.id})
    export_url = reverse("patient-exports", kwargs={"patient_id": patient.id})

    # Warm up to avoid initial auth/session/content-type queries
    client.get(form_url)
    client.get(export_url)

    # 1. Setup 2 items for each list
    create_form_responses(therapist, patient, 2)
    create_clinical_exports(therapist, patient, 2)

    with CaptureQueriesContext(connection) as queries_forms_small:
        response = client.get(form_url)
        assert response.status_code == 200
        count_forms_small = len(queries_forms_small)

    with CaptureQueriesContext(connection) as queries_exports_small:
        response = client.get(export_url)
        assert response.status_code == 200
        count_exports_small = len(queries_exports_small)

    # Clean up before creating larger dataset
    ClinicalFormResponse.objects.all().delete()
    ClinicalExport.objects.all().delete()

    # 2. Setup 5 items for each list
    create_form_responses(therapist, patient, 5)
    create_clinical_exports(therapist, patient, 5)

    with CaptureQueriesContext(connection) as queries_forms_large:
        response = client.get(form_url)
        assert response.status_code == 200
        count_forms_large = len(queries_forms_large)

    with CaptureQueriesContext(connection) as queries_exports_large:
        response = client.get(export_url)
        assert response.status_code == 200
        count_exports_large = len(queries_exports_large)

    print("\nClinical Lists Queries:")
    print(f"Form responses (2 items): {count_forms_small}")
    print(f"Form responses (5 items): {count_forms_large}")
    print(f"Clinical exports (2 items): {count_exports_small}")
    print(f"Clinical exports (5 items): {count_exports_large}")

    # Prior to optimization:
    # - Form responses would execute N+1 queries to retrieve therapist name
    # - Clinical exports would execute N+1 queries to retrieve created_by name
    # After adding select_related, the query count must be constant (equal for small & large datasets).
    assert count_forms_large == count_forms_small
    assert count_exports_large == count_exports_small
