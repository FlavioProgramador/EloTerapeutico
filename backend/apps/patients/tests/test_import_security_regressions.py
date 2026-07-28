from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

from apps.organizations.models import Organization, OrganizationMembership, OrganizationSettings
from apps.patients.models import Patient
from apps.users.models import User


@pytest.fixture
def multi_tenant_setup(db):
    # Tenant A
    user_a = User.objects.create_user(
        email="therapist.a@example.com",
        password="secure-password-a",
        full_name="Therapist A",
        role=User.Role.THERAPIST,
    )
    org_a = Organization.objects.create(
        name="Org A",
        slug="org-a",
        organization_type=Organization.Type.CLINIC,
        status=Organization.Status.ACTIVE,
        created_by=user_a,
    )
    OrganizationSettings.objects.get_or_create(
        organization=org_a,
        business_name_on_documents=org_a.name,
    )
    OrganizationMembership.objects.create(
        organization=org_a,
        user=user_a,
        role=OrganizationMembership.Role.OWNER,
        status=OrganizationMembership.Status.ACTIVE,
    )

    # Tenant B
    user_b = User.objects.create_user(
        email="therapist.b@example.com",
        password="secure-password-b",
        full_name="Therapist B",
        role=User.Role.THERAPIST,
    )
    org_b = Organization.objects.create(
        name="Org B",
        slug="org-b",
        organization_type=Organization.Type.CLINIC,
        status=Organization.Status.ACTIVE,
        created_by=user_b,
    )
    OrganizationSettings.objects.get_or_create(
        organization=org_b,
        business_name_on_documents=org_b.name,
    )
    OrganizationMembership.objects.create(
        organization=org_b,
        user=user_b,
        role=OrganizationMembership.Role.OWNER,
        status=OrganizationMembership.Status.ACTIVE,
    )

    client_a = APIClient()
    client_a.force_authenticate(user_a)
    client_a.credentials(HTTP_X_ORGANIZATION_ID=str(org_a.pk))

    client_b = APIClient()
    client_b.force_authenticate(user_b)
    client_b.credentials(HTTP_X_ORGANIZATION_ID=str(org_b.pk))

    return {
        "user_a": user_a,
        "org_a": org_a,
        "client_a": client_a,
        "user_b": user_b,
        "org_b": org_b,
        "client_b": client_b,
    }


@pytest.mark.django_db
def test_cross_tenant_cpf_uniqueness_probing_is_blocked(multi_tenant_setup):
    setup = multi_tenant_setup
    shared_cpf = "52998224725"

    # Create a patient in Tenant B
    Patient.objects.create(
        organization=setup["org_b"],
        therapist=setup["user_b"],
        full_name="Patient B",
        cpf=shared_cpf,
        birth_date=date(1990, 1, 1),
        status=Patient.Status.ACTIVE,
    )

    # Therapist A tries to create a patient with the SAME CPF in Tenant A.
    # This must succeed because CPF uniqueness is scoped per organization/tenant!
    create_payload = {
        "full_name": "Patient A",
        "cpf": shared_cpf,
        "birth_date": "1995-05-10",
        "status": "active",
        "therapist": setup["user_a"].id,
    }

    url = reverse("patient-list")
    response = setup["client_a"].post(url, create_payload, format="json")
    assert response.status_code == 201, response.data
    assert response.data["cpf"] == shared_cpf


@pytest.mark.django_db
def test_cross_tenant_import_csv_does_not_leak_cpf_existence(multi_tenant_setup):
    setup = multi_tenant_setup
    shared_cpf = "39053344705"

    # Create a patient in Tenant B
    Patient.objects.create(
        organization=setup["org_b"],
        therapist=setup["user_b"],
        full_name="Patient in Org B",
        cpf=shared_cpf,
        birth_date=date(1990, 1, 1),
        status=Patient.Status.ACTIVE,
    )

    # Therapist A previews CSV with the same CPF. It should NOT be flagged as duplicate or leaked!
    csv_content = (
        "full_name,cpf,birth_date,email,phone,gender,status,modality,payer_type\n"
        f"Paciente Importado A,{shared_cpf},1992-04-12,importado.a@example.com,,N,active,online,private\n"
    )

    preview_file = SimpleUploadedFile(
        "pacientes.csv",
        csv_content.encode("utf-8"),
        content_type="text/csv",
    )

    url = reverse("patient-import-csv")
    response = setup["client_a"].post(
        url,
        {"file": preview_file, "confirm": "false"},
        format="multipart",
    )

    assert response.status_code == 200, response.data
    # No duplicates should be detected from other organizations
    assert len(response.data["duplicates"]) == 0
    assert response.data["valid"] == 1


@pytest.mark.django_db
def test_same_tenant_import_csv_correctly_flags_duplicates(multi_tenant_setup):
    setup = multi_tenant_setup
    shared_cpf = "39053344705"

    # Create a patient in Tenant A
    Patient.objects.create(
        organization=setup["org_a"],
        therapist=setup["user_a"],
        full_name="Existing Patient in Org A",
        cpf=shared_cpf,
        birth_date=date(1990, 1, 1),
        status=Patient.Status.ACTIVE,
    )

    # Therapist A previews CSV with the same CPF. It must correctly flag it as duplicate!
    csv_content = (
        "full_name,cpf,birth_date,email,phone,gender,status,modality,payer_type\n"
        f"Paciente Importado A,{shared_cpf},1992-04-12,importado.a@example.com,,N,active,online,private\n"
    )

    preview_file = SimpleUploadedFile(
        "pacientes.csv",
        csv_content.encode("utf-8"),
        content_type="text/csv",
    )

    url = reverse("patient-import-csv")
    response = setup["client_a"].post(
        url,
        {"file": preview_file, "confirm": "false"},
        format="multipart",
    )

    assert response.status_code == 200, response.data
    # Duplicate must be detected since it's the same organization
    assert len(response.data["duplicates"]) == 1
    assert response.data["duplicates"][0]["cpf"] == shared_cpf
