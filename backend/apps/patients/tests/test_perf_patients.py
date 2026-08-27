import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status

from apps.patients.models import Patient


@pytest.mark.django_db
def test_patient_dashboard_metrics_queries_optimized(auth_client, therapist_user):
    for i in range(5):
        Patient.objects.create(
            full_name=f"Paciente Ativo {i}",
            therapist=therapist_user,
            status=Patient.Status.ACTIVE,
        )
    Patient.objects.create(
        full_name="Paciente Encerrado",
        therapist=therapist_user,
        status=Patient.Status.DISCHARGED,
    )

    url = reverse("patient-dashboard-metrics")

    # Prior to optimization:
    # 1 query for active tenant context resolution + 5 queries for count (total, active, discharged, new_current, new_previous) = 6 queries.
    # After optimization:
    # 1 query for active tenant context resolution + 1 query for single aggregate calculation = 2 queries.
    with CaptureQueriesContext(connection) as queries:
        response = auth_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["total"] == 6
    assert response.data["active"] == 5
    assert response.data["discharged"] == 1
    assert response.data["active_percentage"] == 83
    assert response.data["discharged_percentage"] == 17

    assert len(queries) == 2
