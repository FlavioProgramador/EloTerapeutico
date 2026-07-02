from datetime import timedelta

import pytest
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from apps.agenda.models import Appointment
from apps.patients.models import Patient
from apps.records.evolution_flow_models import ClinicalEvolutionTemplate
from apps.records.extended_models import EvolutionClinicalData
from apps.records.models import Evolution
from apps.users.models import User


@pytest.fixture
def therapist(db):
    return User.objects.create_user(
        email="evolution.therapist@example.com",
        password="safe-password",
        full_name="Terapeuta Evolução",
        role=User.Role.THERAPIST,
    )


@pytest.fixture
def patient(therapist):
    return Patient.objects.create(
        full_name="Paciente Evolução",
        therapist=therapist,
        status=Patient.Status.ACTIVE,
    )


@pytest.fixture
def client(therapist):
    api = APIClient()
    api.force_authenticate(therapist)
    return api


def endpoint(patient):
    return f"/api/v1/records/patients/{patient.id}/clinical-evolutions/"


def valid_payload(**overrides):
    payload = {
        "session_date": timezone.localdate().isoformat(),
        "content": "Paciente apresentou melhora e manteve boa adesão.",
        "therapist_observations": "Paciente apresentou melhora e manteve boa adesão.",
        "content_format": "markdown",
        "is_confidential": False,
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_cria_evolucao_e_sanitiza_html(client, patient):
    response = client.post(
        endpoint(patient),
        valid_payload(content="<script>alert(1)</script> **Evolução segura**"),
        format="json",
    )

    assert response.status_code == 201
    evolution = Evolution.objects.get(pk=response.data["id"])
    assert "script" not in evolution.content.lower()
    assert "**Evolução segura**" in evolution.content
    assert response.data["content_format"] == "markdown"


@pytest.mark.django_db
def test_conteudo_e_data_sao_obrigatorios(client, patient):
    missing_content = client.post(
        endpoint(patient),
        {"session_date": timezone.localdate().isoformat(), "content": ""},
        format="json",
    )
    missing_date = client.post(
        endpoint(patient),
        {"content": "Registro clínico"},
        format="json",
    )

    assert missing_content.status_code == 400
    assert missing_date.status_code == 400


@pytest.mark.django_db
def test_bloqueia_data_futura(client, patient):
    response = client.post(
        endpoint(patient),
        valid_payload(session_date=(timezone.localdate() + timedelta(days=1)).isoformat()),
        format="json",
    )

    assert response.status_code == 400
    assert "session_date" in response.data


@pytest.mark.django_db
def test_impede_idor_de_consulta(client, patient, therapist):
    other_patient = Patient.objects.create(
        full_name="Outro Paciente",
        therapist=therapist,
        status=Patient.Status.ACTIVE,
    )
    start = timezone.now() - timedelta(hours=2)
    appointment = Appointment.objects.create(
        patient=other_patient,
        therapist=therapist,
        start_time=start,
        end_time=start + timedelta(minutes=50),
        session_value=150,
    )

    response = client.post(
        endpoint(patient),
        valid_payload(appointment=appointment.id),
        format="json",
    )

    assert response.status_code == 400
    assert "appointment" in response.data


@pytest.mark.django_db
def test_vinculo_com_consulta_do_paciente(client, patient, therapist):
    start = timezone.now() - timedelta(hours=2)
    appointment = Appointment.objects.create(
        patient=patient,
        therapist=therapist,
        start_time=start,
        end_time=start + timedelta(minutes=50),
        session_value=150,
        status=Appointment.Status.COMPLETED,
    )
    response = client.post(
        endpoint(patient),
        valid_payload(
            appointment=appointment.id,
            session_date=timezone.localtime(start).date().isoformat(),
        ),
        format="json",
    )

    assert response.status_code == 201
    assert response.data["appointment"] == appointment.id


@pytest.mark.django_db
def test_edicao_parcial_preserva_conteudo(client, patient):
    created = client.post(endpoint(patient), valid_payload(), format="json")
    response = client.patch(
        f"/api/v1/records/clinical-evolutions/{created.data['id']}/",
        {"is_confidential": True},
        format="json",
    )

    assert response.status_code == 200
    evolution = Evolution.objects.get(pk=created.data["id"])
    assert evolution.content == valid_payload()["content"]
    assert evolution.is_confidential is True
    assert evolution.versions.count() == 1


@pytest.mark.django_db
def test_secretaria_nao_acessa_evolucoes(patient):
    secretary = User.objects.create_user(
        email="secretary@example.com",
        password="safe-password",
        full_name="Secretária",
        role=User.Role.SECRETARY,
    )
    api = APIClient()
    api.force_authenticate(secretary)

    response = api.get(endpoint(patient))

    assert response.status_code == 403


@pytest.mark.django_db
def test_confidencial_exige_permissao_explicita(client, patient, therapist):
    created = client.post(
        endpoint(patient),
        valid_payload(is_confidential=True),
        format="json",
    )
    evolution_id = created.data["id"]
    admin = User.objects.create_user(
        email="clinical.admin@example.com",
        password="safe-password",
        full_name="Administrador Clínico",
        role=User.Role.ADMIN,
    )
    admin_client = APIClient()
    admin_client.force_authenticate(admin)

    denied = admin_client.get(
        f"/api/v1/records/clinical-evolutions/{evolution_id}/"
    )
    permission = Permission.objects.get(
        codename="view_confidential_evolution",
        content_type__app_label="records",
    )
    admin.user_permissions.add(permission)
    allowed = admin_client.get(
        f"/api/v1/records/clinical-evolutions/{evolution_id}/"
    )

    assert denied.status_code == 403
    assert allowed.status_code == 200
    assert allowed.data["created_by"] == therapist.id


@pytest.mark.django_db
def test_upload_valido_e_bloqueio_de_assinatura_invalida(
    client, patient, tmp_path, settings
):
    settings.MEDIA_ROOT = tmp_path
    created = client.post(endpoint(patient), valid_payload(), format="json")
    evolution_id = created.data["id"]
    valid_png = SimpleUploadedFile(
        "evidencia.png",
        b"\x89PNG\r\n\x1a\n" + b"0" * 32,
        content_type="image/png",
    )
    invalid_png = SimpleUploadedFile(
        "falso.png",
        b"arquivo executavel disfarçado",
        content_type="image/png",
    )

    valid = client.post(
        f"/api/v1/records/clinical-evolutions/{evolution_id}/attachments/",
        {"file": valid_png},
        format="multipart",
    )
    invalid = client.post(
        f"/api/v1/records/clinical-evolutions/{evolution_id}/attachments/",
        {"file": invalid_png},
        format="multipart",
    )

    assert valid.status_code == 201
    assert valid.data["original_name"] == "evidencia.png"
    assert invalid.status_code == 400


@pytest.mark.django_db
def test_upload_acima_de_dez_megabytes_e_rejeitado(
    client, patient, tmp_path, settings
):
    settings.MEDIA_ROOT = tmp_path
    created = client.post(endpoint(patient), valid_payload(), format="json")
    oversized = SimpleUploadedFile(
        "grande.pdf",
        b"%PDF-1.7\n" + b"0" * (10 * 1024 * 1024),
        content_type="application/pdf",
    )

    response = client.post(
        f"/api/v1/records/clinical-evolutions/{created.data['id']}/attachments/",
        {"file": oversized},
        format="multipart",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_arquivamento_e_template_privado(client, patient, therapist):
    template = client.post(
        "/api/v1/records/clinical-templates/",
        {"name": "Sessão padrão", "content": "**Objetivo**\n\n- Intervenção"},
        format="json",
    )
    listed = client.get("/api/v1/records/clinical-templates/")
    created = client.post(endpoint(patient), valid_payload(), format="json")
    archived = client.delete(
        f"/api/v1/records/clinical-evolutions/{created.data['id']}/"
    )

    assert template.status_code == 201
    assert ClinicalEvolutionTemplate.objects.get().owner == therapist
    assert listed.status_code == 200
    assert listed.data[0]["name"] == "Sessão padrão"
    assert archived.status_code == 204
    assert (
        EvolutionClinicalData.objects.get(evolution_id=created.data["id"]).status
        == EvolutionClinicalData.Status.ARCHIVED
    )
