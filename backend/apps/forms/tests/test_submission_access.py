import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.forms.models import FormSubmission, TherapeuticForm
from apps.organizations.models import Organization, OrganizationMembership
from apps.patients.models import Patient
from apps.users.models import User


@pytest.fixture
def forms_security_setup(db):
    therapist1 = User.objects.create_user(
        email="therapist1@example.com",
        password="password123",
        full_name="Therapist One",
        role=User.Role.THERAPIST,
    )
    therapist2 = User.objects.create_user(
        email="therapist2@example.com",
        password="password123",
        full_name="Therapist Two",
        role=User.Role.THERAPIST,
    )
    therapist_org2 = User.objects.create_user(
        email="therapist_org2@example.com",
        password="password123",
        full_name="Therapist Org 2",
        role=User.Role.THERAPIST,
    )

    org1 = Organization.objects.create(name="Org One", slug="org-one", created_by=therapist1)
    org2 = Organization.objects.create(name="Org Two", slug="org-two", created_by=therapist_org2)

    OrganizationMembership.objects.create(
        user=therapist1,
        organization=org1,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=True,
    )
    OrganizationMembership.objects.create(
        user=therapist2,
        organization=org1,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=True,
    )
    OrganizationMembership.objects.create(
        user=therapist_org2,
        organization=org2,
        role=OrganizationMembership.Role.THERAPIST,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=True,
    )

    admin1 = User.objects.create_user(
        email="admin1@example.com",
        password="password123",
        full_name="Admin One",
        role=User.Role.ADMIN,
    )
    OrganizationMembership.objects.create(
        user=admin1,
        organization=org1,
        role=OrganizationMembership.Role.ADMIN,
        status=OrganizationMembership.Status.ACTIVE,
        is_default=True,
    )

    patient1 = Patient.objects.create(
        full_name="Patient One",
        therapist=therapist1,
        organization=org1,
    )
    patient2 = Patient.objects.create(
        full_name="Patient Two",
        therapist=therapist2,
        organization=org1,
    )

    # Shared form in org1 accessible by therapist1 and therapist2
    form = TherapeuticForm.objects.create(
        organization=org1,
        owner=therapist1,
        name="Formulário da Clínica",
        created_by=therapist1,
        updated_by=therapist1,
    )

    # Submissions on the form
    sub1 = FormSubmission.objects.create(
        organization=org1,
        form=form,
        owner=therapist1,
        professional=therapist1,
        patient=patient1,
        submitted_by=therapist1,
        status=FormSubmission.Status.SUBMITTED,
    )

    sub2 = FormSubmission.objects.create(
        organization=org1,
        form=form,
        owner=therapist2,
        professional=therapist2,
        patient=patient2,
        submitted_by=therapist2,
        status=FormSubmission.Status.SUBMITTED,
    )

    return {
        "org1": org1,
        "org2": org2,
        "therapist1": therapist1,
        "therapist2": therapist2,
        "therapist_org2": therapist_org2,
        "admin1": admin1,
        "patient1": patient1,
        "patient2": patient2,
        "form": form,
        "sub1": sub1,
        "sub2": sub2,
    }


@pytest.mark.django_db
def test_unauthenticated_user_rejected_from_submission_list(forms_security_setup):
    form = forms_security_setup["form"]
    client = APIClient()

    response = client.get(f"/api/v1/forms/{form.id}/submissions/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_other_organization_therapist_cannot_list_submissions(forms_security_setup):
    form = forms_security_setup["form"]
    therapist_org2 = forms_security_setup["therapist_org2"]
    org2 = forms_security_setup["org2"]
    client = APIClient()
    client.force_authenticate(user=therapist_org2)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org2.id))

    response = client.get(f"/api/v1/forms/{form.id}/submissions/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_therapist_only_sees_own_submissions(forms_security_setup):
    form = forms_security_setup["form"]
    therapist1 = forms_security_setup["therapist1"]
    sub1 = forms_security_setup["sub1"]
    sub2 = forms_security_setup["sub2"]
    org1 = forms_security_setup["org1"]

    client1 = APIClient()
    client1.force_authenticate(user=therapist1)
    client1.credentials(HTTP_X_ORGANIZATION_ID=str(org1.id))

    res = client1.get(f"/api/v1/forms/{form.id}/submissions/")
    assert res.status_code == status.HTTP_200_OK
    data = res.data.get("results", res.data)
    submission_ids = [item["id"] for item in data]
    assert sub1.id in submission_ids
    assert sub2.id not in submission_ids


@pytest.mark.django_db
def test_admin_can_see_all_submissions_for_form(forms_security_setup):
    form = forms_security_setup["form"]
    admin1 = forms_security_setup["admin1"]
    sub1 = forms_security_setup["sub1"]
    sub2 = forms_security_setup["sub2"]
    org1 = forms_security_setup["org1"]

    client = APIClient()
    client.force_authenticate(user=admin1)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org1.id))

    res = client.get(f"/api/v1/forms/{form.id}/submissions/")
    assert res.status_code == status.HTTP_200_OK
    data = res.data.get("results", res.data)
    submission_ids = [item["id"] for item in data]
    assert sub1.id in submission_ids
    assert sub2.id in submission_ids
