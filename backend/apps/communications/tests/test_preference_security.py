from unittest.mock import patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.organizations.models import Organization, OrganizationMembership
from apps.patients.models import Patient
from apps.users.models import User


class CommunicationPreferenceSecurityTests(TestCase):
    def setUp(self):
        self.therapist_a = User.objects.create_user(
            email="therapist.a@elo.test",
            password="password123",
            full_name="Therapist A",
            role=User.Role.THERAPIST,
        )

        self.organization = Organization.objects.create(
            name="Clínica Elo",
            slug="clinica-elo",
            created_by=self.therapist_a,
        )

        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.therapist_a,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )

        self.therapist_b = User.objects.create_user(
            email="therapist.b@elo.test",
            password="password123",
            full_name="Therapist B",
            role=User.Role.THERAPIST,
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.therapist_b,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )

        self.patient_a = Patient.objects.create(
            organization=self.organization,
            therapist=self.therapist_a,
            full_name="Paciente A",
            email="paciente.a@test.com",
        )

        self.patient_b = Patient.objects.create(
            organization=self.organization,
            therapist=self.therapist_b,
            full_name="Paciente B",
            email="paciente.b@test.com",
        )

        self.client_a = APIClient()
        self.client_a.force_authenticate(user=self.therapist_a)
        self.client_a.credentials(HTTP_X_ORGANIZATION_ID=str(self.organization.id))

    @patch("apps.communications.permissions.enforce_communication_access")
    def test_unauthenticated_access_rejected(self, mock_enforce):
        client = APIClient()
        url = f"/api/v1/communications/preferences/patient/{self.patient_a.pk}/"
        response = client.get(url, HTTP_X_ORGANIZATION_ID=str(self.organization.id))
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    @patch("apps.communications.permissions.enforce_communication_access")
    def test_therapist_can_access_own_patient_preferences(self, mock_enforce):
        url = f"/api/v1/communications/preferences/patient/{self.patient_a.pk}/"
        response = self.client_a.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["patient"], self.patient_a.pk)

    @patch("apps.communications.permissions.enforce_communication_access")
    def test_cross_therapist_idor_access_rejected_with_404(self, mock_enforce):
        # Therapist A attempting to access Patient B's communication preferences
        url = f"/api/v1/communications/preferences/patient/{self.patient_b.pk}/"
        response = self.client_a.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("apps.communications.permissions.enforce_communication_access")
    def test_cross_therapist_idor_patch_rejected_with_404(self, mock_enforce):
        # Therapist A attempting to update Patient B's communication preferences
        url = f"/api/v1/communications/preferences/patient/{self.patient_b.pk}/"
        response = self.client_a.patch(
            url,
            {"whatsapp_enabled": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
