import pytest
from rest_framework import status
from rest_framework.test import APIClient

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
        organization_type=Organization.Type.INDIVIDUAL,
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


def test_unauthenticated_requests_are_rejected():
    client = APIClient()

    # Tentativa de acesso sem autenticação deve retornar 401
    anamnesis_url = "/api/v1/records/patients/999/anamnesis/"
    response = client.get(anamnesis_url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    workspace_url = "/api/v1/records/patients/999/workspace/"
    response = client.get(workspace_url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_cross_tenant_patient_lookup_returns_404_not_found():
    # Usuário A e Org A
    user_a = create_user("therapist_a@test.com", "Therapist A")
    org_a, _ = create_organization(user_a, "Tenant A")

    # Usuário B e Org B
    user_b = create_user("therapist_b@test.com", "Therapist B")
    org_b, _ = create_organization(user_b, "Tenant B")

    # Paciente B pertence à Org B e terapeuta B
    patient_b = Patient.objects.create(
        organization=org_b,
        therapist=user_b,
        full_name="Patient B of Tenant B",
    )

    client = APIClient()
    # Forçar autenticação como usuário A (Tenant A)
    client.force_authenticate(user_a)

    # Forçar cabeçalho de organização se necessário (o middleware resolve)
    # Tentar ler a anamnese do Paciente B (deve dar 404, não 403 ou revelar que existe)
    anamnesis_url = f"/api/v1/records/patients/{patient_b.pk}/anamnesis/"
    response = client.get(anamnesis_url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Tentar ler o workspace do Paciente B (deve dar 404)
    workspace_url = f"/api/v1/records/patients/{patient_b.pk}/workspace/"
    response = client.get(workspace_url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_legitimate_owner_can_access_their_own_patient():
    # Usuário A e Org A
    user_a = create_user("therapist_a@test.com", "Therapist A")
    org_a, _ = create_organization(user_a, "Tenant A")

    # Paciente A pertence à Org A e terapeuta A
    patient_a = Patient.objects.create(
        organization=org_a,
        therapist=user_a,
        full_name="Patient A of Tenant A",
    )

    client = APIClient()
    client.force_authenticate(user_a)

    # Ler workspace do Paciente A deve retornar sucesso (200 OK)
    workspace_url = f"/api/v1/records/patients/{patient_a.pk}/workspace/"
    response = client.get(workspace_url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["patient"]["full_name"] == "Patient A of Tenant A"

    # Ler anamnese do Paciente A (como não foi criada, deve retornar 404 com detalhe específico da anamnese, não do paciente)
    anamnesis_url = f"/api/v1/records/patients/{patient_a.pk}/anamnesis/"
    response = client.get(anamnesis_url)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["detail"] == "Anamnese não encontrada para este paciente."
