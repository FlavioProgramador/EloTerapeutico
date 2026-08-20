import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.forms.models import FieldType, FormField, FormSubmission, TherapeuticForm
from apps.organizations.models import Organization, OrganizationMembership
from apps.patients.models import Patient
from apps.users.models import User

pytestmark = pytest.mark.django_db


def create_user(email: str, name: str) -> User:
    return User.objects.create_user(
        email=email,
        full_name=name,
        password="TestPassword123!",
        role=User.Role.THERAPIST,
    )


def create_organization(owner: User, name: str) -> tuple[Organization, OrganizationMembership]:
    org = Organization.objects.create(
        name=name,
        slug=name.lower().replace(" ", "-"),
        organization_type=Organization.Type.CLINIC,
        created_by=owner,
    )
    membership = OrganizationMembership.objects.create(
        organization=org,
        user=owner,
        role=OrganizationMembership.Role.OWNER,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=True,
    )
    return org, membership


def add_therapist_to_organization(org: Organization, user: User) -> OrganizationMembership:
    return OrganizationMembership.objects.create(
        organization=org,
        user=user,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=True,
    )


def test_unauthenticated_submission_list_requests_are_rejected():
    client = APIClient()
    response = client.get("/api/v1/forms/999/submissions/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_therapist_cannot_list_submissions_belonging_to_another_therapist():
    # 1. Setup Org and two therapists in same org
    owner = create_user("owner@test.com", "Owner Therapist")
    org, _ = create_organization(owner, "Clínica Teste")

    therapist_b = create_user("therapist_b@test.com", "Therapist B")
    add_therapist_to_organization(org, therapist_b)

    # Patients
    patient_a = Patient.objects.create(organization=org, therapist=owner, full_name="Patient A")
    patient_b = Patient.objects.create(organization=org, therapist=therapist_b, full_name="Patient B")

    # Form owned by therapist_b
    form = TherapeuticForm.objects.create(
        organization=org,
        owner=therapist_b,
        name="Formulário de Avaliação",
        created_by=therapist_b,
        updated_by=therapist_b,
    )
    FormField.objects.create(
        form=form,
        type=FieldType.SHORT_TEXT,
        label="Sintomas",
        order=1,
    )

    # Submissions on therapist_b's form
    sub_a = FormSubmission.objects.create(
        organization=org,
        form=form,
        patient=patient_a,
        professional=owner,
        owner=owner,
        submitted_by=owner,
    )
    sub_b = FormSubmission.objects.create(
        organization=org,
        form=form,
        patient=patient_b,
        professional=therapist_b,
        owner=therapist_b,
        submitted_by=therapist_b,
    )

    client = APIClient()
    client.force_authenticate(therapist_b)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    response = client.get(f"/api/v1/forms/{form.pk}/submissions/")
    assert response.status_code == status.HTTP_200_OK

    results = response.data.get("results", response.data)
    returned_ids = [item["id"] for item in results]

    # Therapist B should only see sub_b, not sub_a
    assert sub_b.pk in returned_ids
    assert sub_a.pk not in returned_ids


def test_cross_tenant_therapist_cannot_access_form_submissions():
    user_a = create_user("therapist_a@test.com", "Therapist A")
    org_a, _ = create_organization(user_a, "Org A")

    user_b = create_user("therapist_b@test.com", "Therapist B")
    org_b, _ = create_organization(user_b, "Org B")

    form_a = TherapeuticForm.objects.create(
        organization=org_a,
        owner=user_a,
        name="Formulário Org A",
        created_by=user_a,
        updated_by=user_a,
    )

    client = APIClient()
    client.force_authenticate(user_b)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org_b.id))

    response = client.get(f"/api/v1/forms/{form_a.pk}/submissions/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
