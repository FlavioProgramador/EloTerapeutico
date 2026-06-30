from datetime import date
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

from apps.patients.models import Patient
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

    response = client.get(
        reverse("patient-dashboard", kwargs={"pk": foreign_patient.id})
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_exportacao_csv_nao_expoe_cpf_completo(dashboard_context):
    client, _, patient, _ = dashboard_context

    response = client.get(reverse("patient-export-csv"))
    content = b"".join(response.streaming_content).decode("utf-8") if response.streaming else response.content.decode("utf-8")

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
