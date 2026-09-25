import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.organizations.models import Organization, OrganizationMembership
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
def test_evolution_viewset_unauthenticated_rejected():
    """
    Ensure unauthenticated requests to evolution endpoint are rejected.
    """
    client = APIClient()
    response = client.get("/api/v1/records/evolutions/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_evolution_viewset_cross_tenant_admin_blocked():
    """
    Regression: An admin of org1 cannot list or retrieve evolutions of patients in org2.
    """
    admin1 = User.objects.create_user(
        email="admin1@org1.test",
        password="password",
        full_name="Admin Org 1",
        role=User.Role.ADMIN,
    )
    therapist2 = User.objects.create_user(
        email="therapist2@org2.test",
        password="password",
        full_name="Therapist Org 2",
        role=User.Role.THERAPIST,
    )

    org1 = Organization.objects.create(name="Org 1", slug="org-1", created_by=admin1)
    org2 = Organization.objects.create(name="Org 2", slug="org-2", created_by=therapist2)

    OrganizationMembership.objects.create(
        organization=org1,
        user=admin1,
        role=OrganizationMembership.Role.ADMIN,
        status=OrganizationMembership.Status.ACTIVE,
    )
    OrganizationMembership.objects.create(
        organization=org2,
        user=therapist2,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
    )

    patient2 = Patient.objects.create(
        organization=org2,
        full_name="Patient Org 2",
        therapist=therapist2,
        status=Patient.Status.ACTIVE,
    )
    ev2 = Evolution.objects.create(
        patient=patient2,
        content="Note Org 2",
        session_date=timezone.localdate(),
        created_by=therapist2,
    )

    client = APIClient()
    client.force_authenticate(admin1)

    # List request without patient_id
    response_list = client.get("/api/v1/records/evolutions/")
    assert response_list.status_code == 200
    results = response_list.data.get("results", response_list.data)
    assert not any(item["id"] == ev2.id for item in results)

    # Detail request
    response_detail = client.get(f"/api/v1/records/evolutions/{ev2.id}/")
    assert response_detail.status_code == 404


@pytest.mark.django_db
def test_evolution_viewset_same_tenant_admin_allowed():
    """
    An admin of org1 can list non-confidential evolutions of patients in org1.
    """
    admin1 = User.objects.create_user(
        email="admin1_legit@org1.test",
        password="password",
        full_name="Admin Legitimate",
        role=User.Role.ADMIN,
    )
    org1 = Organization.objects.create(name="Org 1", slug="org-1-legit", created_by=admin1)
    OrganizationMembership.objects.create(
        organization=org1,
        user=admin1,
        role=OrganizationMembership.Role.ADMIN,
        status=OrganizationMembership.Status.ACTIVE,
    )

    therapist1 = User.objects.create_user(
        email="therapist1@org1.test",
        password="password",
        full_name="Therapist Org 1",
        role=User.Role.THERAPIST,
    )
    OrganizationMembership.objects.create(
        organization=org1,
        user=therapist1,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
    )

    patient1 = Patient.objects.create(
        organization=org1,
        full_name="Patient Org 1",
        therapist=therapist1,
        status=Patient.Status.ACTIVE,
    )
    ev1 = Evolution.objects.create(
        patient=patient1,
        content="Note Org 1",
        session_date=timezone.localdate(),
        created_by=therapist1,
    )

    client = APIClient()
    client.force_authenticate(admin1)

    response_list = client.get("/api/v1/records/evolutions/")
    assert response_list.status_code == 200
    results = response_list.data.get("results", response_list.data)
    assert any(item["id"] == ev1.id for item in results)
