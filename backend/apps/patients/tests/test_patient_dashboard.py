from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

from django.contrib.auth.models import Permission
from apps.patients.models import Patient
from apps.records.models import Evolution
from apps.users.models import User


@pytest.fixture
def dashboard_context(db):
    therapist = User.objects.create_user(
        email="dashboard-therapist@example.com",
        password="safe-password",
        full_name="Terapeuta de Teste",
        role=User.Role.THERAPIST,
    )
    other = User.objects.create_user(
        email="dashboard-other@example.com",
        password="safe-password",
        full_name="Outro Terapeuta",
        role=User.Role.THERAPIST,
    )
    patient = Patient.objects.create(
        full_name="Paciente Fictício",
        cpf="52998224725",
        birth_date=date(1994, 5, 10),
        therapist=therapist,
        status=Patient.Status.ACTIVE,
        phone="21999999999",
        tags=["Particular", "Online"],
    )
    foreign_patient = Patient.objects.create(
        full_name="Paciente de Outro Profissional",
        cpf="11144477735",
        birth_date=date(1988, 3, 15),
        therapist=other,
        status=Patient.Status.ACTIVE,
    )
    client = APIClient()
    client.force_authenticate(therapist)
    return client, therapist, patient, foreign_patient


@pytest.mark.django_db
def test_listagem_mascara_cpf_e_isola_terapeuta(dashboard_context):
    client, _, patient, foreign_patient = dashboard_context

    response = client.get(reverse("patient-list"))

    assert response.status_code == 200
    ids = [item["id"] for item in response.data["results"]]
    assert patient.id in ids
    assert foreign_patient.id not in ids
    item = next(item for item in response.data["results"] if item["id"] == patient.id)
    assert item["masked_cpf"] == "529.***.***-25"
    assert "cpf" not in item


@pytest.mark.django_db
def test_metricas_usam_todo_queryset_autorizado(dashboard_context):
    client, therapist, _, _ = dashboard_context
    Patient.objects.create(
        full_name="Paciente Encerrado",
        cpf="12345678909",
        birth_date=date(1985, 1, 1),
        therapist=therapist,
        status=Patient.Status.DISCHARGED,
    )

    response = client.get(reverse("patient-dashboard-metrics"))

    assert response.status_code == 200
    assert response.data["total"] == 2
    assert response.data["active"] == 1
    assert response.data["discharged"] == 1


@pytest.mark.django_db
def test_painel_lateral_rejeita_paciente_de_outro_terapeuta(dashboard_context):
    client, _, _, foreign_patient = dashboard_context

    response = client.get(reverse("patient-dashboard", kwargs={"pk": foreign_patient.id}))

    assert response.status_code == 404


@pytest.mark.django_db
def test_exportacao_csv_nao_expoe_cpf_completo(dashboard_context):
    client, _, patient, _ = dashboard_context

    response = client.get(reverse("patient-export-csv"))
    content = (
        b"".join(response.streaming_content).decode("utf-8") if response.streaming else response.content.decode("utf-8")
    )

    assert response.status_code == 200
    assert patient.cpf not in content
    assert patient.masked_cpf in content


@pytest.mark.django_db
def test_importacao_csv_exige_preview_antes_de_confirmar(dashboard_context):
    client, _, _, _ = dashboard_context
    csv_content = (
        "full_name,cpf,birth_date,email,phone,gender,status,modality,payer_type\n"
        "Paciente Importado,390.533.447-05,1992-04-12,importado@example.com,,N,active,online,private\n"
    )

    preview_file = SimpleUploadedFile(
        "pacientes.csv",
        csv_content.encode("utf-8"),
        content_type="text/csv",
    )
    preview = client.post(
        reverse("patient-import-csv"),
        {"file": preview_file, "confirm": "false"},
        format="multipart",
    )

    assert preview.status_code == 200
    assert preview.data["valid"] == 1
    assert Patient.objects.filter(full_name="Paciente Importado").count() == 0

    confirm_file = SimpleUploadedFile(
        "pacientes.csv",
        csv_content.encode("utf-8"),
        content_type="text/csv",
    )
    confirmed = client.post(
        reverse("patient-import-csv"),
        {"file": confirm_file, "confirm": "true"},
        format="multipart",
    )

    assert confirmed.status_code == 201
    assert confirmed.data["imported"] == 1
    assert Patient.objects.filter(full_name="Paciente Importado").exists()


@pytest.mark.django_db
def test_dashboard_oculta_evolucao_confidencial_para_terapeuta_sem_permissao(dashboard_context):
    client, therapist, patient, _ = dashboard_context

    colleague = User.objects.create_user(
        email="dashboard-colleague@example.com",
        password="safe-password",
        full_name="Colega de Equipe",
        role=User.Role.THERAPIST,
    )

    public_evolution = Evolution.objects.create(
        patient=patient,
        created_by=therapist,
        session_date=date(2026, 1, 10),
        content="Evolução pública inicial",
        is_confidential=False,
    )

    confidential_evolution = Evolution.objects.create(
        patient=patient,
        created_by=colleague,
        session_date=date(2026, 1, 15),
        content="Anotações confidenciais sensíveis do colega",
        is_confidential=True,
    )

    # 1. Usuário não autenticado é rejeitado
    unauthenticated_client = APIClient()
    response_unauth = unauthenticated_client.get(reverse("patient-dashboard", kwargs={"pk": patient.id}))
    assert response_unauth.status_code == 401

    # 2. Terapeuta sem permissão explícita e não autor da evolução confidencial não vê o resumo confidencial
    response = client.get(reverse("patient-dashboard", kwargs={"pk": patient.id}))
    assert response.status_code == 200
    assert response.data["latest_evolution"]["id"] == public_evolution.id
    assert response.data["latest_evolution"]["summary"] == "Evolução pública inicial"

    # 3. Autor da evolução confidencial (therapist) cria sua própria evolução confidencial mais recente
    own_confidential = Evolution.objects.create(
        patient=patient,
        created_by=therapist,
        session_date=date(2026, 1, 20),
        content="Minha própria evolução confidencial",
        is_confidential=True,
    )
    response_own = client.get(reverse("patient-dashboard", kwargs={"pk": patient.id}))
    assert response_own.status_code == 200
    assert response_own.data["latest_evolution"]["id"] == own_confidential.id
    assert response_own.data["latest_evolution"]["summary"] == "Minha própria evolução confidencial"

    # 4. Usuário com permissão explícita `records.view_confidential_evolution` vê a evolução confidencial de terceiros se for a mais recente
    own_confidential.delete()
    permission = Permission.objects.get(codename="view_confidential_evolution")
    therapist.user_permissions.add(permission)
    therapist = User.objects.get(pk=therapist.pk)
    client.force_authenticate(therapist)

    response_perm = client.get(reverse("patient-dashboard", kwargs={"pk": patient.id}))
    assert response_perm.status_code == 200
    assert response_perm.data["latest_evolution"]["id"] == confidential_evolution.id
    assert response_perm.data["latest_evolution"]["summary"] == "Anotações confidenciais sensíveis do colega"
