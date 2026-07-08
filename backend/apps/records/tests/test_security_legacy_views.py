import pytest
from django.contrib.auth.models import Permission
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.patients.models import Patient, PatientProfessional
from apps.records.models import Evolution, Anamnesis
from apps.users.models import User

@pytest.fixture
def owner(db):
    return User.objects.create_user(
        email="owner@example.com",
        password="password",
        full_name="Owner Therapist",
        role=User.Role.THERAPIST,
    )

@pytest.fixture
def shared_therapist(db):
    return User.objects.create_user(
        email="shared@example.com",
        password="password",
        full_name="Shared Therapist",
        role=User.Role.THERAPIST,
    )

@pytest.fixture
def other_therapist(db):
    return User.objects.create_user(
        email="other@example.com",
        password="password",
        full_name="Other Therapist",
        role=User.Role.THERAPIST,
    )

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@example.com",
        password="password",
        full_name="Admin User",
        role=User.Role.ADMIN,
    )

@pytest.fixture
def patient(owner):
    return Patient.objects.create(
        full_name="Test Patient",
        therapist=owner,
        status=Patient.Status.ACTIVE,
    )

@pytest.fixture
def link(patient, shared_therapist, owner):
    return PatientProfessional.objects.create(
        patient=patient,
        professional=shared_therapist,
        assigned_by=owner,
        is_active=True
    )

@pytest.mark.django_db
def test_anamnesis_view_shared_access_allowed(owner, shared_therapist, patient, link):
    """
    Regression: AnamnesisView._get_patient now allows shared therapists.
    """
    Anamnesis.objects.create(
        patient=patient,
        chief_complaint="Complaint",
        created_by=owner
    )

    client = APIClient()
    client.force_authenticate(shared_therapist)

    url = f"/api/v1/records/patients/{patient.id}/anamnesis/"
    response = client.get(url)

    assert response.status_code == 200

@pytest.mark.django_db
def test_evolution_viewset_shared_access_allowed(owner, shared_therapist, patient, link):
    """
    Regression: EvolutionViewSet.get_queryset now allows shared therapists.
    """
    Evolution.objects.create(
        patient=patient,
        content="Note",
        session_date=timezone.localdate(),
        created_by=owner
    )

    client = APIClient()
    client.force_authenticate(shared_therapist)

    url = f"/api/v1/records/evolutions/?patient={patient.id}"
    response = client.get(url)

    assert response.status_code == 200

@pytest.mark.django_db
def test_evolution_viewset_confidentiality_enforced(owner, other_therapist, patient):
    """
    Regression: EvolutionViewSet filters out confidential evolutions from other therapists.
    """
    ev = Evolution.objects.create(
        patient=patient,
        content="Secret note",
        session_date=timezone.localdate(),
        created_by=other_therapist,
        is_confidential=True
    )

    client = APIClient()
    client.force_authenticate(owner) # owner of the patient

    url = f"/api/v1/records/evolutions/?patient={patient.id}"
    response = client.get(url)

    assert response.status_code == 200
    results = response.data.get("results", response.data)
    assert not any(item["id"] == ev.id for item in results)

@pytest.mark.django_db
def test_evolution_viewset_admin_confidentiality_enforced(admin_user, owner, patient):
    """
    Regression: Admin cannot see confidential evolutions without explicit permission.
    """
    ev = Evolution.objects.create(
        patient=patient,
        content="Secret note",
        session_date=timezone.localdate(),
        created_by=owner,
        is_confidential=True
    )

    client = APIClient()
    client.force_authenticate(admin_user)

    url = f"/api/v1/records/evolutions/{ev.id}/"
    response = client.get(url)

    assert response.status_code == 404 # Because it's filtered from queryset

@pytest.mark.django_db
def test_evolution_viewset_admin_edit_blocked(admin_user, owner, patient):
    """
    Regression: Admin cannot edit notes they didn't create.
    """
    ev = Evolution.objects.create(
        patient=patient,
        content="Original note",
        session_date=timezone.localdate(),
        created_by=owner
    )

    client = APIClient()
    client.force_authenticate(admin_user)

    url = f"/api/v1/records/evolutions/{ev.id}/"
    response = client.patch(url, {"content": "Edited by admin"}, format="json")

    assert response.status_code == 403
    ev.refresh_from_db()
    assert ev.content == "Original note"
