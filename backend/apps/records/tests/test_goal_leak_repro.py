from datetime import date
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import User
from apps.patients.models import Patient, PatientProfessional
from apps.records.models import Evolution
from apps.records.treatment_models import TreatmentGoal

@pytest.mark.django_db
def test_goal_leaks_confidential_evolution_id():
    # Therapist A (Owner)
    therapist_a = User.objects.create_user(
        email="a@example.com",
        password="password",
        full_name="Therapist A",
        role=User.Role.THERAPIST,
    )
    # Therapist B (Linked)
    therapist_b = User.objects.create_user(
        email="b@example.com",
        password="password",
        full_name="Therapist B",
        role=User.Role.THERAPIST,
    )

    # Patient owned by A, linked to B
    patient = Patient.objects.create(
        full_name="Patient X",
        cpf="12345678901",
        birth_date=date(1990, 1, 1),
        therapist=therapist_a,
    )
    PatientProfessional.objects.create(
        patient=patient,
        professional=therapist_b,
        is_active=True,
        assigned_by=therapist_a,
    )

    # Confidential evolution by A
    conf_evolution = Evolution.objects.create(
        patient=patient,
        created_by=therapist_a,
        content="Sensitive Data",
        session_date=date.today(),
        is_confidential=True
    )

    # Goal created by A, linked to confidential evolution
    goal = TreatmentGoal.objects.create(
        patient=patient,
        title="Sensitive Goal",
        created_by=therapist_a
    )
    goal.evolutions.add(conf_evolution)

    client = APIClient()
    client.force_authenticate(therapist_b)

    # Therapist B views goals
    url = f"/api/v1/records/patients/{patient.id}/goals/"
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK

    # Check if confidential evolution ID is in the response
    goal_data = response.data[0]
    assert conf_evolution.id not in goal_data["evolutions"], f"Confidential evolution ID {conf_evolution.id} leaked to therapist B"

    # Also check workspace endpoint
    workspace_url = f"/api/v1/records/patients/{patient.id}/workspace/"
    ws_response = client.get(workspace_url)
    assert ws_response.status_code == status.HTTP_200_OK
    ws_goal_data = ws_response.data["goals"][0]
    assert conf_evolution.id not in ws_goal_data["evolutions"], f"Confidential evolution ID {conf_evolution.id} leaked to therapist B in workspace"

    # Also check detail endpoint
    detail_url = f"/api/v1/records/goals/{goal.id}/"
    detail_response = client.get(detail_url)
    assert detail_response.status_code == status.HTTP_200_OK
    assert conf_evolution.id not in detail_response.data["evolutions"], f"Confidential evolution ID {conf_evolution.id} leaked to therapist B in goal detail"
