import pytest
from django.urls import reverse
from rest_framework import status

from apps.organizations.models import Organization, OrganizationMembership
from apps.patients.models import Patient, PatientProfessional
from apps.users.models import User


@pytest.fixture
def therapist_primary(db):
    user = User.objects.create_user(
        email="primary@test.com",
        full_name="Primary Therapist",
        password="password123",
        role=User.Role.THERAPIST,
    )
    org = Organization.objects.create(
        name="Org A",
        slug="org-a",
        organization_type=Organization.Type.CLINIC,
        status=Organization.Status.ACTIVE,
        created_by=user,
    )
    OrganizationMembership.objects.create(
        organization=org,
        user=user,
        role=OrganizationMembership.Role.OWNER,
        status=OrganizationMembership.Status.ACTIVE,
    )
    return user


@pytest.fixture
def organization(therapist_primary):
    return therapist_primary.organization_memberships.first().organization


@pytest.fixture
def therapist_shared(db, organization):
    user = User.objects.create_user(
        email="shared@test.com",
        full_name="Shared Therapist",
        password="password123",
        role=User.Role.THERAPIST,
    )
    OrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
    )
    return user


@pytest.fixture
def therapist_unlinked(db, organization):
    user = User.objects.create_user(
        email="unlinked@test.com",
        full_name="Unlinked Therapist",
        password="password123",
        role=User.Role.THERAPIST,
    )
    OrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
    )
    return user


@pytest.fixture
def viewer_user(db, organization):
    user = User.objects.create_user(
        email="viewer@test.com",
        full_name="Viewer User",
        password="password123",
        role=User.Role.SECRETARY,
    )
    OrganizationMembership.objects.create(
        organization=organization,
        user=user,
        role=OrganizationMembership.Role.VIEWER,
        status=OrganizationMembership.Status.ACTIVE,
    )
    return user


@pytest.fixture
def other_org_user(db):
    user = User.objects.create_user(
        email="other@test.com",
        full_name="Other Org Therapist",
        password="password123",
        role=User.Role.THERAPIST,
    )
    other_org = Organization.objects.create(
        name="Org B",
        slug="org-b",
        organization_type=Organization.Type.CLINIC,
        status=Organization.Status.ACTIVE,
        created_by=user,
    )
    OrganizationMembership.objects.create(
        organization=other_org,
        user=user,
        role=OrganizationMembership.Role.OWNER,
        status=OrganizationMembership.Status.ACTIVE,
    )
    return user


@pytest.fixture
def patient(therapist_primary, organization):
    return Patient.objects.create(
        organization=organization,
        full_name="Test Patient",
        therapist=therapist_primary,
        status=Patient.Status.ACTIVE,
    )


@pytest.fixture
def shared_link(patient, therapist_shared, therapist_primary):
    return PatientProfessional.objects.create(
        patient=patient,
        professional=therapist_shared,
        assigned_by=therapist_primary,
        is_active=True,
    )


@pytest.mark.django_db
class TestPatientReminderSecurity:
    def test_unauthenticated_user_cannot_update_reminders(self, api_client, patient):
        url = reverse("patient-reminders", kwargs={"pk": patient.pk})
        response = api_client.patch(url, {"enabled": False}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_primary_therapist_can_update_reminders(self, api_client, therapist_primary, organization, patient):
        api_client.force_authenticate(user=therapist_primary)
        api_client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.pk))
        url = reverse("patient-reminders", kwargs={"pk": patient.pk})
        response = api_client.patch(url, {"enabled": False}, format="json")
        assert response.status_code == status.HTTP_200_OK
        patient.refresh_from_db()
        assert patient.reminders_enabled is False

    def test_shared_therapist_can_update_reminders(
        self, api_client, therapist_shared, organization, patient, shared_link
    ):
        api_client.force_authenticate(user=therapist_shared)
        api_client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.pk))
        url = reverse("patient-reminders", kwargs={"pk": patient.pk})
        response = api_client.patch(url, {"enabled": False}, format="json")
        assert response.status_code == status.HTTP_200_OK
        patient.refresh_from_db()
        assert patient.reminders_enabled is False

    def test_unlinked_therapist_cannot_update_reminders(
        self, api_client, therapist_unlinked, organization, patient
    ):
        api_client.force_authenticate(user=therapist_unlinked)
        api_client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.pk))
        url = reverse("patient-reminders", kwargs={"pk": patient.pk})
        response = api_client.patch(url, {"enabled": False}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_without_update_capability_is_rejected(
        self, api_client, viewer_user, organization, patient
    ):
        api_client.force_authenticate(user=viewer_user)
        api_client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.pk))
        url = reverse("patient-reminders", kwargs={"pk": patient.pk})
        response = api_client.patch(url, {"enabled": False}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_other_organization_user_cannot_update_reminders(self, api_client, other_org_user, patient):
        other_org = other_org_user.organization_memberships.first().organization
        api_client.force_authenticate(user=other_org_user)
        api_client.credentials(HTTP_X_ORGANIZATION_ID=str(other_org.pk))
        url = reverse("patient-reminders", kwargs={"pk": patient.pk})
        response = api_client.patch(url, {"enabled": False}, format="json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
