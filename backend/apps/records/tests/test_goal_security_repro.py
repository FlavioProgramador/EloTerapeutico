from datetime import date

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.patients.models import Patient, PatientProfessional
from apps.records.treatment_models import TreatmentGoal
from apps.users.models import User


@pytest.fixture
def security_context(db):
    owner = User.objects.create_user(
        email="owner@example.com",
        password="password",
        full_name="Owner Therapist",
        role=User.Role.THERAPIST,
    )
    linked = User.objects.create_user(
        email="linked@example.com",
        password="password",
        full_name="Linked Therapist",
        role=User.Role.THERAPIST,
    )
    patient = Patient.objects.create(
        full_name="Patient Name",
        cpf="12345678901",
        birth_date=date(1990, 1, 1),
        therapist=owner,
    )
    PatientProfessional.objects.create(
        patient=patient,
        professional=linked,
        is_active=True,
        assigned_by=owner,
    )
    goal = TreatmentGoal.objects.create(
        patient=patient,
        title="Original Title",
        created_by=owner,
    )
    return owner, linked, patient, goal

@pytest.mark.django_db
def test_linked_therapist_cannot_modify_goal_of_another_author(security_context):
    owner, linked, patient, goal = security_context
    client = APIClient()
    client.force_authenticate(linked)

    # Attempt to modify the goal title
    response = client.patch(
        f"/api/v1/records/goals/{goal.id}/",
        {"title": "Modified by Linked"},
        format="json"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    goal.refresh_from_db()
    assert goal.title == "Original Title"

@pytest.mark.django_db
def test_linked_therapist_cannot_delete_goal_of_another_author(security_context):
    owner, linked, patient, goal = security_context
    client = APIClient()
    client.force_authenticate(linked)

    # Attempt to delete the goal
    response = client.delete(f"/api/v1/records/goals/{goal.id}/")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    goal.refresh_from_db()
    assert goal.status != TreatmentGoal.Status.ARCHIVED

@pytest.mark.django_db
def test_owner_can_modify_own_goal(security_context):
    owner, linked, patient, goal = security_context
    client = APIClient()
    client.force_authenticate(owner)

    response = client.patch(
        f"/api/v1/records/goals/{goal.id}/",
        {"title": "New Title"},
        format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    goal.refresh_from_db()
    assert goal.title == "New Title"

@pytest.mark.django_db
def test_unauthenticated_user_is_rejected(security_context):
    owner, linked, patient, goal = security_context
    client = APIClient()

    response = client.patch(
        f"/api/v1/records/goals/{goal.id}/",
        {"title": "New Title"},
        format="json"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
