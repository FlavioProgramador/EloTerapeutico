from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.communications.models import CommunicationPreference
from apps.organizations.models import Organization, OrganizationMembership
from apps.patients.models import Patient
from apps.users.models import User

pytestmark = pytest.mark.django_db


def create_user_and_org(email: str) -> User:
    current_user = User.objects.create_user(
        email=email,
        password="SenhaForte123!",
        full_name="Usuário Teste",
    )
    slug = email.split("@", 1)[0].replace(".", "-")
    organization = Organization.objects.create(
        name=f"Organização de {current_user.full_name}",
        slug=slug,
        organization_type=Organization.Type.INDIVIDUAL,
        status=Organization.Status.ACTIVE,
        created_by=current_user,
    )
    OrganizationMembership.objects.create(
        organization=organization,
        user=current_user,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=True,
    )
    current_user.test_organization = organization
    return current_user


def authenticated_client(current_user: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(current_user)
    client.credentials(
        HTTP_X_ORGANIZATION_ID=str(current_user.test_organization.pk)
    )
    return client


def test_unauthenticated_requests_are_rejected():
    client = APIClient()
    response_list = client.get("/api/v1/communications/preferences/")
    response_detail = client.get("/api/v1/communications/preferences/patient/1/")

    assert response_list.status_code in (401, 403)
    assert response_detail.status_code in (401, 403)


def test_cross_tenant_patient_preference_access_is_rejected():
    therapist1 = create_user_and_org("therapist1@tenant1.test")
    therapist2 = create_user_and_org("therapist2@tenant2.test")

    patient2 = Patient.objects.create(
        organization=therapist2.test_organization,
        therapist=therapist2,
        full_name="Paciente Tenant 2",
    )

    client1 = authenticated_client(therapist1)

    response_get = client1.get(
        f"/api/v1/communications/preferences/patient/{patient2.pk}/"
    )
    response_patch = client1.patch(
        f"/api/v1/communications/preferences/patient/{patient2.pk}/",
        {"allow_whatsapp": True},
        format="json",
    )

    assert response_get.status_code == 404
    assert response_patch.status_code == 404


def test_cross_therapist_patient_preference_access_is_rejected_in_same_tenant():
    therapist1 = create_user_and_org("therapist1@sharedorg.test")
    org = therapist1.test_organization

    therapist2 = User.objects.create_user(
        email="therapist2@sharedorg.test",
        password="SenhaForte123!",
        full_name="Segundo Terapeuta",
    )
    OrganizationMembership.objects.create(
        organization=org,
        user=therapist2,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=True,
    )
    therapist2.test_organization = org

    patient_of_therapist2 = Patient.objects.create(
        organization=org,
        therapist=therapist2,
        full_name="Paciente do Terapeuta 2",
    )

    client1 = authenticated_client(therapist1)

    # Therapist 1 attempts to access/update preference of Patient 2
    response_get = client1.get(
        f"/api/v1/communications/preferences/patient/{patient_of_therapist2.pk}/"
    )
    response_patch = client1.patch(
        f"/api/v1/communications/preferences/patient/{patient_of_therapist2.pk}/",
        {"allow_whatsapp": True},
        format="json",
    )

    assert response_get.status_code == 404
    assert response_patch.status_code == 404


def test_legitimate_therapist_can_access_and_update_patient_preference():
    therapist = create_user_and_org("legit-therapist@org.test")
    patient = Patient.objects.create(
        organization=therapist.test_organization,
        therapist=therapist,
        full_name="Paciente Legítimo",
    )

    client = authenticated_client(therapist)

    # GET creates or fetches preference
    response_get = client.get(
        f"/api/v1/communications/preferences/patient/{patient.pk}/"
    )
    assert response_get.status_code == 200
    assert response_get.data["patient"] == patient.pk
    assert response_get.data["allow_whatsapp"] is False

    # PATCH updates preference
    response_patch = client.patch(
        f"/api/v1/communications/preferences/patient/{patient.pk}/",
        {"allow_whatsapp": True},
        format="json",
    )
    assert response_patch.status_code == 200
    assert response_patch.data["allow_whatsapp"] is True


def test_preference_list_filters_by_accessible_patients():
    therapist1 = create_user_and_org("therapist1-list@org.test")
    org = therapist1.test_organization

    therapist2 = User.objects.create_user(
        email="therapist2-list@org.test",
        password="SenhaForte123!",
        full_name="Segundo Terapeuta List",
    )
    OrganizationMembership.objects.create(
        organization=org,
        user=therapist2,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=True,
    )
    therapist2.test_organization = org

    patient1 = Patient.objects.create(
        organization=org,
        therapist=therapist1,
        full_name="Paciente 1",
    )
    patient2 = Patient.objects.create(
        organization=org,
        therapist=therapist2,
        full_name="Paciente 2",
    )

    CommunicationPreference.objects.create(
        organization=org,
        owner=therapist1,
        patient=patient1,
    )
    CommunicationPreference.objects.create(
        organization=org,
        owner=therapist2,
        patient=patient2,
    )

    client1 = authenticated_client(therapist1)
    response = client1.get("/api/v1/communications/preferences/")

    assert response.status_code == 200
    patient_ids = [item["patient"] for item in response.data]
    assert patient1.pk in patient_ids
    assert patient2.pk not in patient_ids
