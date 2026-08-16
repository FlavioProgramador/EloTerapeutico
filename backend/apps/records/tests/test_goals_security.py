import pytest
from django.urls import reverse
from rest_framework import status

from apps.organizations.models import Organization, OrganizationMembership
from apps.patients.models import Patient
from apps.records.treatment_models import TreatmentGoal
from apps.users.models import User


@pytest.mark.django_db
class TestTreatmentGoalSecurity:
    @pytest.fixture(autouse=True)
    def setup_data(self, default_password):
        self.therapist_a = User.objects.create_user(
            email="therapist_a@example.com",
            full_name="Therapist A",
            password=default_password,
            role=User.Role.THERAPIST,
        )
        self.org_a = Organization.objects.create(
            name="Org A",
            slug="org-a",
            organization_type=Organization.Type.CLINIC,
            status=Organization.Status.ACTIVE,
            created_by=self.therapist_a,
        )
        OrganizationMembership.objects.create(
            user=self.therapist_a,
            organization=self.org_a,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )

        self.patient_a = Patient.objects.create(
            organization=self.org_a,
            therapist=self.therapist_a,
            full_name="Paciente Org A",
        )
        self.goal_a = TreatmentGoal.objects.create(
            organization=self.org_a,
            patient=self.patient_a,
            created_by=self.therapist_a,
            title="Meta do Paciente A",
        )

        # Organization B & Therapist B
        self.therapist_b = User.objects.create_user(
            email="therapist_b@example.com",
            full_name="Therapist B",
            password=default_password,
            role=User.Role.THERAPIST,
        )
        self.org_b = Organization.objects.create(
            name="Org B",
            slug="org-b",
            organization_type=Organization.Type.CLINIC,
            status=Organization.Status.ACTIVE,
            created_by=self.therapist_b,
        )
        OrganizationMembership.objects.create(
            user=self.therapist_b,
            organization=self.org_b,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )

        self.patient_b = Patient.objects.create(
            organization=self.org_b,
            therapist=self.therapist_b,
            full_name="Paciente Org B",
        )
        self.goal_b = TreatmentGoal.objects.create(
            organization=self.org_b,
            patient=self.patient_b,
            created_by=self.therapist_b,
            title="Meta do Paciente B",
        )

    def test_unauthenticated_request_rejected(self, api_client):
        url = reverse("treatment-goal-detail", kwargs={"pk": self.goal_a.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cross_tenant_goal_returns_404(self, api_client):
        """Impede IDOR e existência de IDs entre tenants/usuários não autorizados."""
        api_client.force_authenticate(user=self.therapist_b)
        url = reverse("treatment-goal-detail", kwargs={"pk": self.goal_a.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        response_patch = api_client.patch(url, {"title": "Tentativa de alteração"})
        assert response_patch.status_code == status.HTTP_404_NOT_FOUND

        response_delete = api_client.delete(url)
        assert response_delete.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthorized_therapist_same_org_returns_404(self, api_client, default_password):
        """Therapist in same org but not linked to patient receives 404."""
        therapist_other = User.objects.create_user(
            email="other_therapist@example.com",
            full_name="Therapist Other",
            password=default_password,
            role=User.Role.THERAPIST,
        )
        OrganizationMembership.objects.create(
            user=therapist_other,
            organization=self.org_a,
            role=OrganizationMembership.Role.THERAPIST,
            status=OrganizationMembership.Status.ACTIVE,
        )

        api_client.force_authenticate(user=therapist_other)
        url = reverse("treatment-goal-detail", kwargs={"pk": self.goal_a.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_authorized_user_can_access_goal(self, api_client):
        api_client.force_authenticate(user=self.therapist_a)
        url = reverse("treatment-goal-detail", kwargs={"pk": self.goal_a.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Meta do Paciente A"

        response_patch = api_client.patch(url, {"title": "Meta Atualizada"})
        assert response_patch.status_code == status.HTTP_200_OK
        assert response_patch.data["title"] == "Meta Atualizada"

        response_delete = api_client.delete(url)
        assert response_delete.status_code == status.HTTP_204_NO_CONTENT
