from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.organizations.models import Organization, OrganizationMembership
from apps.patients.models import Patient
from apps.scheduling.models import Appointment, PatientPackage
from apps.users.models import User


@pytest.fixture
def user_a(db):
    return User.objects.create_user(
        email="user_a@test.com",
        password="Password123!",
        full_name="Therapist A",
        role=User.Role.THERAPIST,
    )


@pytest.fixture
def user_b(db):
    return User.objects.create_user(
        email="user_b@test.com",
        password="Password123!",
        full_name="Therapist B",
        role=User.Role.THERAPIST,
    )


@pytest.fixture
def org_a(db, user_a):
    org = Organization.objects.create(name="Org A", slug="org-a", created_by=user_a)
    OrganizationMembership.objects.create(
        user=user_a,
        organization=org,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
    )
    return org


@pytest.fixture
def org_b(db, user_b):
    org = Organization.objects.create(name="Org B", slug="org-b", created_by=user_b)
    OrganizationMembership.objects.create(
        user=user_b,
        organization=org,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
    )
    return org


@pytest.fixture
def patient_a(db, org_a, user_a):
    return Patient.objects.create(
        organization=org_a,
        therapist=user_a,
        full_name="Patient A",
        status=Patient.Status.ACTIVE,
        is_active=True,
    )


@pytest.fixture
def patient_b(db, org_b, user_b):
    return Patient.objects.create(
        organization=org_b,
        therapist=user_b,
        full_name="Patient B",
        status=Patient.Status.ACTIVE,
        is_active=True,
    )


@pytest.fixture
def package_a(db, org_a, user_a, patient_a):
    return PatientPackage.objects.create(
        organization=org_a,
        therapist=user_a,
        patient=patient_a,
        name="Pacote A",
        sessions_contracted=10,
        total_value=Decimal("1000.00"),
    )


@pytest.fixture
def client_a(user_a, org_a):
    api = APIClient()
    api.force_authenticate(user=user_a)
    api.credentials(HTTP_X_ORGANIZATION_ID=str(org_a.pk))
    return api


@pytest.fixture
def client_b(user_b, org_b):
    api = APIClient()
    api.force_authenticate(user=user_b)
    api.credentials(HTTP_X_ORGANIZATION_ID=str(org_b.pk))
    return api


@pytest.mark.django_db
def test_unauthenticated_user_rejected_on_add_session(package_a):
    client = APIClient()
    url = reverse("patient-package-add-session", kwargs={"pk": package_a.pk})
    response = client.post(url, {}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_other_tenant_therapist_rejected_on_add_session(client_b, package_a):
    url = reverse("patient-package-add-session", kwargs={"pk": package_a.pk})
    start = timezone.now() + timedelta(days=2)
    payload = {
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(minutes=50)).isoformat(),
        "session_value": "100.00",
    }
    response = client_b.post(url, payload, format="json")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_legitimate_therapist_can_add_session_to_own_package(client_a, package_a, patient_a, user_a):
    url = reverse("patient-package-add-session", kwargs={"pk": package_a.pk})
    start = timezone.now() + timedelta(days=2)
    payload = {
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(minutes=50)).isoformat(),
        "session_value": "100.00",
    }
    response = client_a.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    appointment = Appointment.objects.get(pk=response.data["id"])
    assert appointment.patient == patient_a
    assert appointment.therapist == user_a
    assert appointment.package == package_a


@pytest.mark.django_db
def test_add_session_overrides_malicious_patient_and_therapist_data(client_a, package_a, patient_b, user_b, patient_a, user_a):
    url = reverse("patient-package-add-session", kwargs={"pk": package_a.pk})
    start = timezone.now() + timedelta(days=3)
    payload = {
        "patient": patient_b.id,
        "therapist": user_b.id,
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(minutes=50)).isoformat(),
        "session_value": "100.00",
    }
    response = client_a.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    appointment = Appointment.objects.get(pk=response.data["id"])
    assert appointment.patient == patient_a
    assert appointment.therapist == user_a
    assert appointment.package == package_a
