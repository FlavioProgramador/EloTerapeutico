
import pytest
from django.urls import reverse
from rest_framework import status
from apps.users.models import User
from apps.patients.models import Patient, PatientProfessional

@pytest.fixture
def therapist_primary(db):
    return User.objects.create_user(
        email="primary@test.com",
        full_name="Primary Therapist",
        password="password123",
        role=User.Role.THERAPIST,
    )

@pytest.fixture
def therapist_shared(db):
    return User.objects.create_user(
        email="shared@test.com",
        full_name="Shared Therapist",
        password="password123",
        role=User.Role.THERAPIST,
    )

@pytest.fixture
def therapist_unlinked(db):
    return User.objects.create_user(
        email="unlinked@test.com",
        full_name="Unlinked Therapist",
        password="password123",
        role=User.Role.THERAPIST,
    )

@pytest.fixture
def patient(therapist_primary):
    return Patient.objects.create(
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
        is_active=True
    )

@pytest.mark.django_db
class TestPatientReminderSecurity:
    def test_shared_therapist_can_update_reminders(self, api_client, therapist_shared, patient, shared_link):
        """
        FAILING TEST: Currently shared therapists are denied access because the view
        only checks for direct ownership (patient.therapist == user).
        """
        api_client.force_authenticate(user=therapist_shared)
        url = reverse("patient-reminders", kwargs={"pk": patient.pk})

        response = api_client.patch(url, {"enabled": False}, format="json")

        # Currently this returns 404 because of:
        # if user.is_therapist:
        #     queryset = queryset.filter(therapist=user)
        assert response.status_code == status.HTTP_200_OK
        patient.refresh_from_db()
        assert patient.reminders_enabled is False

    def test_unlinked_therapist_cannot_update_reminders(self, api_client, therapist_unlinked, patient):
        api_client.force_authenticate(user=therapist_unlinked)
        url = reverse("patient-reminders", kwargs={"pk": patient.pk})

        response = api_client.patch(url, {"enabled": False}, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated_user_cannot_update_reminders(self, api_client, patient):
        url = reverse("patient-reminders", kwargs={"pk": patient.pk})

        response = api_client.patch(url, {"enabled": False}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
