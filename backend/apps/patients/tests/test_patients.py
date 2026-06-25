"""
Testes de integridade, validação e isolamento de dados do
módulo de Pacientes (CRM).
"""

import pytest
import random
from django.urls import reverse
from rest_framework import status
from datetime import date, timedelta

from apps.users.models import User
from apps.patients.models import Patient


def generate_valid_cpf() -> str:
    """Gera um número de CPF matematicamente válido (11 dígitos)."""
    nine_digits = [random.randint(0, 9) for _ in range(9)]

    # Primeiro dígito verificador
    soma = sum(nine_digits[i] * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11
    if d1 >= 10:
        d1 = 0
    nine_digits.append(d1)

    # Segundo dígito verificador
    soma = sum(nine_digits[i] * (11 - i) for i in range(10))
    d2 = (soma * 10) % 11
    if d2 >= 10:
        d2 = 0
    nine_digits.append(d2)

    return "".join(map(str, nine_digits))


def format_cpf(cpf: str) -> str:
    """Formata um CPF de 11 dígitos para o formato XXX.XXX.XXX-XX."""
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


@pytest.fixture
def other_therapist(db):
    """Outro usuário terapeuta para testes de isolamento."""
    return User.objects.create_user(
        email="outro_terapeuta@teste.com",
        full_name="Dr. Outro Terapeuta",
        password="senha_segura_123",
        role=User.Role.THERAPIST,
        crp_number="06/654321",
    )


@pytest.fixture
def patient_data():
    """Dados padrão para criação de um paciente adulto."""
    valid_cpf = generate_valid_cpf()
    return {
        "full_name": "Paciente Teste Adulto",
        "cpf": format_cpf(valid_cpf),
        "birth_date": "1990-01-01",
        "gender": "M",
        "email": "adulto@teste.com",
        "phone": "(11) 99999-9999",
        "address": {"street": "Rua Teste, 123"},
        "status": "active",
        "notes": "Notas iniciais do paciente adulto.",
    }


@pytest.fixture
def patient_of_therapist(therapist_user):
    """Paciente vinculado ao terapeuta padrão."""
    valid_cpf = generate_valid_cpf()
    return Patient.objects.create(
        full_name="Paciente do Terapeuta",
        cpf=valid_cpf,
        birth_date=date(1995, 5, 5),
        gender="F",
        email="paciente_terapeuta@teste.com",
        phone="11988887777",
        therapist=therapist_user,
        status=Patient.Status.ACTIVE,
    )


@pytest.fixture
def patient_of_other_therapist(other_therapist):
    """Paciente vinculado ao outro terapeuta."""
    valid_cpf = generate_valid_cpf()
    return Patient.objects.create(
        full_name="Paciente do Outro",
        cpf=valid_cpf,
        birth_date=date(1993, 3, 3),
        gender="M",
        email="paciente_outro@teste.com",
        phone="11977776666",
        therapist=other_therapist,
        status=Patient.Status.ACTIVE,
    )


@pytest.mark.django_db
class TestPatientCreation:
    """
    Testes focados na criação de pacientes e validações de
    regras de negócio.
    """

    def test_create_patient_adult(self, auth_client, patient_data):
        url = reverse("patient-list")
        response = auth_client.post(url, patient_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["full_name"] == patient_data["full_name"]

        # CPF deve ser armazenado limpo (apenas dígitos)
        expected_clean_cpf = (
            patient_data["cpf"].replace(".", "").replace("-", "")
        )
        assert response.data["cpf"] == expected_clean_cpf

    def test_create_patient_minor_requires_guardian(
        self, auth_client, patient_data
    ):
        url = reverse("patient-list")
        data = patient_data.copy()

        # Define nascimento para menor de idade (ex: 10 anos atrás)
        minor_birth = date.today() - timedelta(days=365 * 10)
        data["birth_date"] = minor_birth.isoformat()
        data["full_name"] = "Paciente Menor Sem Responsavel"
        data["cpf"] = format_cpf(generate_valid_cpf())

        # Tentar salvar sem dados do responsável legal deve
        # falhar (regra de negócio)
        response = auth_client.post(url, data, format="json")
        assert (
            response.status_code == status.HTTP_400_BAD_REQUEST
        ), response.data
        assert "guardian_name" in response.data["error"]["details"]

    def test_create_patient_minor_success(self, auth_client, patient_data):
        url = reverse("patient-list")
        data = patient_data.copy()

        minor_birth = date.today() - timedelta(days=365 * 10)
        data["birth_date"] = minor_birth.isoformat()
        data["full_name"] = "Paciente Menor Com Responsavel"
        data["cpf"] = format_cpf(generate_valid_cpf())
        data["guardian_name"] = "Responsável Legal"

        guardian_cpf = generate_valid_cpf()
        data["guardian_cpf"] = format_cpf(guardian_cpf)

        response = auth_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["guardian_name"] == "Responsável Legal"
        assert response.data["guardian_cpf"] == guardian_cpf


@pytest.mark.django_db
class TestPatientIsolationAndPermissions:
    """
    Testes para garantir isolamento (multi-tenancy) e controle
    de permissões (RBAC).
    """

    def test_therapist_cannot_access_other_therapist_patient(
        self, auth_client, patient_of_other_therapist
    ):
        # Tenta visualizar o paciente de outro terapeuta
        url = reverse(
            "patient-detail", kwargs={"pk": patient_of_other_therapist.pk}
        )
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Tenta editar o paciente de outro terapeuta
        response = auth_client.patch(
            url, {"full_name": "Nome Alterado"}, format="json"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Tenta deletar/arquivar o paciente de outro terapeuta
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_therapist_can_access_own_patient(
        self, auth_client, patient_of_therapist
    ):
        url = reverse("patient-detail", kwargs={"pk": patient_of_therapist.pk})
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == patient_of_therapist.full_name

    def test_secretary_permissions(
        self, api_client, secretary_user, patient_of_therapist, therapist_user
    ):
        api_client.force_authenticate(user=secretary_user)

        # Secretária pode listar
        list_url = reverse("patient-list")
        response = api_client.get(list_url)
        assert response.status_code == status.HTTP_200_OK

        # Secretária pode detalhar cadastro
        detail_url = reverse(
            "patient-detail", kwargs={"pk": patient_of_therapist.pk}
        )
        response = api_client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK

        # Secretária pode criar paciente vinculando ao terapeuta
        create_data = {
            "full_name": "Paciente Criado por Secretaria",
            "cpf": format_cpf(generate_valid_cpf()),
            "birth_date": "1985-05-15",
            "therapist": therapist_user.id,
            "status": "active",
        }
        response = api_client.post(list_url, create_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data

        # Secretária NÃO pode deletar/arquivar
        response = api_client.delete(detail_url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_has_full_access(self, admin_client, patient_of_therapist):
        # Admin pode detalhar
        url = reverse("patient-detail", kwargs={"pk": patient_of_therapist.pk})
        response = admin_client.get(url)
        assert response.status_code == status.HTTP_200_OK

        # Admin pode arquivar (soft-delete)
        response = admin_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestPatientSoftDeleteAndRestore:
    """
    Testes para o fluxo de desativação (soft delete) e
    restauração de pacientes.
    """

    def test_soft_delete_flow(self, auth_client, patient_of_therapist):
        # Inicialmente ativo
        assert patient_of_therapist.is_active is True
        assert patient_of_therapist.deleted_at is None

        # Realiza soft delete chamando a rota de deactivate
        url = reverse(
            "patient-deactivate", kwargs={"pk": patient_of_therapist.pk}
        )
        response = auth_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        # Recarrega do banco usando manager AllPatients
        patient_of_therapist.refresh_from_db()
        assert patient_of_therapist.is_active is False
        assert patient_of_therapist.deleted_at is not None
        assert patient_of_therapist.status == Patient.Status.INACTIVE

        # Na busca comum (PatientManager), ele não deve mais aparecer
        list_url = reverse("patient-list")
        response = auth_client.get(list_url)
        results = response.data.get("results", [])
        assert not any(p["id"] == patient_of_therapist.id for p in results)

    def test_restore_flow(self, auth_client, patient_of_therapist):
        # Executa soft-delete
        patient_of_therapist.soft_delete()

        # Restaura chamando a rota de restore
        url = reverse(
            "patient-restore", kwargs={"pk": patient_of_therapist.pk}
        )
        response = auth_client.post(url)
        assert response.status_code == status.HTTP_200_OK

        # Recarrega e valida estado
        patient_of_therapist.refresh_from_db()
        assert patient_of_therapist.is_active is True
        assert patient_of_therapist.deleted_at is None
        assert patient_of_therapist.status == Patient.Status.ACTIVE


@pytest.mark.django_db
class TestPatientFiltering:
    """Testes para busca e filtragem de pacientes."""

    def test_search_by_name_and_cpf(self, auth_client, therapist_user):
        cpf1 = generate_valid_cpf()
        cpf2 = generate_valid_cpf()

        p1 = Patient.objects.create(
            full_name="João Silva",
            cpf=cpf1,
            birth_date=date(1990, 1, 1),
            therapist=therapist_user,
            status=Patient.Status.ACTIVE,
        )
        p2 = Patient.objects.create(
            full_name="Maria Souza",
            cpf=cpf2,
            birth_date=date(1985, 2, 2),
            therapist=therapist_user,
            status=Patient.Status.ACTIVE,
        )

        url = reverse("patient-list")

        # Busca por "João"
        response = auth_client.get(url, {"search": "João"})
        assert response.status_code == status.HTTP_200_OK
        results = response.data.get("results", [])
        assert len(results) == 1
        assert results[0]["id"] == p1.id

        # Busca por CPF
        response = auth_client.get(url, {"search": cpf2})
        results = response.data.get("results", [])
        assert len(results) == 1
        assert results[0]["id"] == p2.id
