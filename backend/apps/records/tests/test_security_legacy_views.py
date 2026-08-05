import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.patients.models import Patient, PatientProfessional
from apps.records.models import Anamnesis, Evolution
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
        patient=patient, professional=shared_therapist, assigned_by=owner, is_active=True
    )


@pytest.mark.django_db
def test_anamnesis_view_shared_access_allowed(owner, shared_therapist, patient, link):
    """
    Regression: AnamnesisView._get_patient now allows shared therapists.
    """
    Anamnesis.objects.create(patient=patient, chief_complaint="Complaint", created_by=owner)

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
    Evolution.objects.create(patient=patient, content="Note", session_date=timezone.localdate(), created_by=owner)

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
        is_confidential=True,
    )

    client = APIClient()
    client.force_authenticate(owner)  # owner of the patient

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
        is_confidential=True,
    )

    client = APIClient()
    client.force_authenticate(admin_user)

    url = f"/api/v1/records/evolutions/{ev.id}/"
    response = client.get(url)

    assert response.status_code == 404  # Because it's filtered from queryset


@pytest.mark.django_db
def test_evolution_viewset_admin_edit_blocked(admin_user, owner, patient):
    """
    Regression: Admin cannot edit notes they didn't create.
    """
    ev = Evolution.objects.create(
        patient=patient,
        content="Original note",
        session_date=timezone.localdate(),
        created_by=owner,
    )

    client = APIClient()
    client.force_authenticate(admin_user)

    url = f"/api/v1/records/evolutions/{ev.id}/"
    response = client.patch(url, {"content": "Edited by admin"}, format="json")

    assert response.status_code == 403
    ev.refresh_from_db()
    assert ev.content == "Original note"


@pytest.mark.django_db
def test_anamnesis_put_cannot_reassign_patient(owner, patient):
    """
    Regression: Ensure that PUT/PATCH cannot reassign the patient of an existing anamnesis.
    """
    # Create another patient owned by owner
    other_patient = Patient.objects.create(
        full_name="Other Patient",
        therapist=owner,
        status=Patient.Status.ACTIVE,
    )

    anamnesis = Anamnesis.objects.create(
        patient=patient,
        chief_complaint="Complaint A",
        created_by=owner,
    )

    client = APIClient()
    client.force_authenticate(owner)

    url = f"/api/v1/records/patients/{patient.id}/anamnesis/"

    # Try PUT request reassigning patient_id to other_patient
    response = client.put(url, {
        "patient_id": other_patient.id,
        "chief_complaint": "Modified Complaint",
    }, format="json")

    assert response.status_code == 400
    assert "patient_id" in response.data["error"]["details"]

    anamnesis.refresh_from_db()
    assert anamnesis.patient == patient


@pytest.mark.django_db
def test_evolution_add_addendum_restricted_to_author(owner, shared_therapist, other_therapist, patient, link):
    """
    Regression: Ensure only the creator of the evolution can add an addendum.
    """
    ev = Evolution.objects.create(
        patient=patient,
        content="Original clinical note",
        session_date=timezone.localdate(),
        created_by=owner,
        is_locked=True,  # Locked so we can add an addendum
    )

    url = f"/api/v1/records/evolutions/{ev.id}/addendum/"

    # 1. Unrelated therapist tries to add an addendum -> 404 Not Found (no patient access)
    client_unrelated = APIClient()
    client_unrelated.force_authenticate(other_therapist)
    response_unrelated = client_unrelated.post(url, {
        "reason": "Correction",
        "content": "Addendum text by unrelated therapist",
    }, format="json")
    assert response_unrelated.status_code == 404

    # 2. Shared therapist (who has patient access but is not the author) -> 403 Forbidden
    client_shared = APIClient()
    client_shared.force_authenticate(shared_therapist)
    response_shared = client_shared.post(url, {
        "reason": "Correction",
        "content": "Addendum text by shared therapist",
    }, format="json")
    assert response_shared.status_code == 403

    # 3. Original owner tries to add an addendum -> 201 Created
    client_owner = APIClient()
    client_owner.force_authenticate(owner)

    response_owner = client_owner.post(url, {
        "reason": "Correction",
        "content": "Addendum text by original author",
    }, format="json")

    assert response_owner.status_code == 201
    assert response_owner.data["content"] == "Addendum text by original author"
