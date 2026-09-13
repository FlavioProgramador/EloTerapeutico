from datetime import timedelta
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.organizations.models import Organization, OrganizationMembership
from apps.users.models import User

pytestmark = pytest.mark.django_db


def test_check_availability_unauthenticated_rejected():
    client = APIClient()
    url = reverse("appointment-check-availability")
    response = client.post(
        url,
        {
            "date": str(timezone.localdate()),
            "duration": 50,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_check_availability_cross_tenant_therapist_rejected():
    admin_a = User.objects.create_user(
        email="admin-a@example.test",
        full_name="Admin Tenant A",
        password="TestPass2026!",
        role=User.Role.ADMIN,
    )
    org_a = Organization.objects.create(
        name="Org A",
        slug="org-a",
        organization_type=Organization.Type.CLINIC,
        created_by=admin_a,
    )
    OrganizationMembership.objects.create(
        organization=org_a,
        user=admin_a,
        role=OrganizationMembership.Role.ADMIN,
        status=OrganizationMembership.Status.ACTIVE,
    )
    therapist_a = User.objects.create_user(
        email="therapist-a@example.test",
        full_name="Therapist Tenant A",
        password="TestPass2026!",
        role=User.Role.THERAPIST,
    )
    OrganizationMembership.objects.create(
        organization=org_a,
        user=therapist_a,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
    )

    therapist_b = User.objects.create_user(
        email="therapist-b@example.test",
        full_name="Therapist Tenant B",
        password="TestPass2026!",
        role=User.Role.THERAPIST,
    )
    org_b = Organization.objects.create(
        name="Org B",
        slug="org-b",
        organization_type=Organization.Type.CLINIC,
        created_by=therapist_b,
    )
    OrganizationMembership.objects.create(
        organization=org_b,
        user=therapist_b,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
    )

    client = APIClient()
    client.force_authenticate(admin_a)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org_a.pk))

    target_date = str(timezone.localdate() + timedelta(days=1))
    url = reverse("appointment-check-availability")

    response_foreign = client.post(
        url,
        {
            "date": target_date,
            "duration": 50,
            "therapist_id": therapist_b.pk,
        },
        format="json",
    )
    assert response_foreign.status_code == status.HTTP_404_NOT_FOUND

    response_legit = client.post(
        url,
        {
            "date": target_date,
            "duration": 50,
            "therapist_id": therapist_a.pk,
        },
        format="json",
    )
    assert response_legit.status_code == status.HTTP_200_OK
