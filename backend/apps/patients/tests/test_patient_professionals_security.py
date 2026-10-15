import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.organizations.models import Organization, OrganizationMembership, OrganizationSettings
from apps.users.models import User


@pytest.fixture
def multi_tenant_professionals_setup(db):
    # Tenant A
    admin_a = User.objects.create_user(
        email="admin.a@example.com",
        password="secure-password-admin-a",
        full_name="Admin A",
        role=User.Role.ADMIN,
    )
    therapist_a1 = User.objects.create_user(
        email="therapist.a1@example.com",
        password="secure-password-a1",
        full_name="Therapist A1",
        role=User.Role.THERAPIST,
    )
    therapist_a2 = User.objects.create_user(
        email="therapist.a2@example.com",
        password="secure-password-a2",
        full_name="Therapist A2",
        role=User.Role.THERAPIST,
    )
    org_a = Organization.objects.create(
        name="Org A",
        slug="org-a",
        organization_type=Organization.Type.CLINIC,
        status=Organization.Status.ACTIVE,
        created_by=admin_a,
    )
    OrganizationSettings.objects.get_or_create(
        organization=org_a,
        business_name_on_documents=org_a.name,
    )
    OrganizationMembership.objects.create(
        organization=org_a,
        user=admin_a,
        role=OrganizationMembership.Role.ADMIN,
        status=OrganizationMembership.Status.ACTIVE,
    )
    OrganizationMembership.objects.create(
        organization=org_a,
        user=therapist_a1,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
    )
    OrganizationMembership.objects.create(
        organization=org_a,
        user=therapist_a2,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
    )

    # Tenant B
    admin_b = User.objects.create_user(
        email="admin.b@example.com",
        password="secure-password-admin-b",
        full_name="Admin B",
        role=User.Role.ADMIN,
    )
    therapist_b1 = User.objects.create_user(
        email="therapist.b1@example.com",
        password="secure-password-b1",
        full_name="Therapist B1",
        role=User.Role.THERAPIST,
    )
    org_b = Organization.objects.create(
        name="Org B",
        slug="org-b",
        organization_type=Organization.Type.CLINIC,
        status=Organization.Status.ACTIVE,
        created_by=admin_b,
    )
    OrganizationSettings.objects.get_or_create(
        organization=org_b,
        business_name_on_documents=org_b.name,
    )
    OrganizationMembership.objects.create(
        organization=org_b,
        user=admin_b,
        role=OrganizationMembership.Role.ADMIN,
        status=OrganizationMembership.Status.ACTIVE,
    )
    OrganizationMembership.objects.create(
        organization=org_b,
        user=therapist_b1,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
    )

    client_admin_a = APIClient()
    client_admin_a.force_authenticate(admin_a)
    client_admin_a.credentials(HTTP_X_ORGANIZATION_ID=str(org_a.pk))

    client_admin_b = APIClient()
    client_admin_b.force_authenticate(admin_b)
    client_admin_b.credentials(HTTP_X_ORGANIZATION_ID=str(org_b.pk))

    return {
        "admin_a": admin_a,
        "therapist_a1": therapist_a1,
        "therapist_a2": therapist_a2,
        "org_a": org_a,
        "client_admin_a": client_admin_a,
        "admin_b": admin_b,
        "therapist_b1": therapist_b1,
        "org_b": org_b,
        "client_admin_b": client_admin_b,
    }


@pytest.mark.django_db
def test_unauthenticated_user_cannot_access_professionals():
    client = APIClient()
    url = reverse("patient-professionals")
    response = client.get(url)
    assert response.status_code == 401


@pytest.mark.django_db
def test_admin_only_sees_therapists_from_own_tenant(multi_tenant_professionals_setup):
    setup = multi_tenant_professionals_setup
    url = reverse("patient-professionals")

    # Admin of Org A requests professionals list
    response = setup["client_admin_a"].get(url)
    assert response.status_code == 200, response.data

    returned_ids = {p["id"] for p in response.data}
    assert setup["therapist_a1"].pk in returned_ids
    assert setup["therapist_a2"].pk in returned_ids
    # Therapists from Org B MUST NOT be present
    assert setup["therapist_b1"].pk not in returned_ids

    # Admin of Org B requests professionals list
    response_b = setup["client_admin_b"].get(url)
    assert response_b.status_code == 200, response_b.data

    returned_ids_b = {p["id"] for p in response_b.data}
    assert setup["therapist_b1"].pk in returned_ids_b
    assert setup["therapist_a1"].pk not in returned_ids_b
    assert setup["therapist_a2"].pk not in returned_ids_b
