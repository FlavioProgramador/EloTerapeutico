from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from apps.agenda.models import Appointment
from apps.patients.models import Patient
from apps.records.models import Evolution
from apps.users.models import User


@pytest.fixture
def therapist(db):
    return User.objects.create_user(
        email="modal.therapist@example.com",
        password="safe-password",
        full_name="Terapeuta Modal",
        role=User.Role.THERAPIST,
    )


@pytest.fixture
def patient(therapist):
    return Patient.objects.create(
        full_name="Paciente Modal",
        therapist=therapist,
        status=Patient.Status.ACTIVE,
    )


@pytest.fixture
def api(therapist):
    client = APIClient()
    client.force_authenticate(therapist)
    return client


def endpoint(patient):
    return f"/api/v1/records/patients/{patient.id}/clinical-evolutions/"


def valid_payload(**overrides):
    data = {
        "session_date": timezone.localdate().isoformat(),
        "content": "Paciente apresentou melhora e boa adesão.",
        "therapist_observations": "Paciente apresentou melhora e boa adesão.",
        "is_confidential": False,
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_cria_e_sanitiza_evolucao(api, patient):
    response = api.post(
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
def test_valida_data_e_conteudo(api, patient):
    empty = api.post(
        endpoint(patient),
        {"session_date": timezone.localdate().isoformat(), "content": ""},
        format="json",
    )
    future = api.post(
        endpoint(patient),
        valid_payload(session_date=(timezone.localdate() + timedelta(days=1)).isoformat()),
        format="json",
    )

    assert empty.status_code == 400
    assert future.status_code == 400


@pytest.mark.django_db
def test_impede_consulta_de_outro_paciente(api, patient, therapist):
    other = Patient.objects.create(
        full_name="Outro Paciente",
        therapist=therapist,
        status=Patient.Status.ACTIVE,
    )
    start = timezone.now() - timedelta(hours=2)
    appointment = Appointment.objects.create(
        patient=other,
        therapist=therapist,
        start_time=start,
        end_time=start + timedelta(minutes=50),
        session_value=150,
    )

    response = api.post(
        endpoint(patient),
        valid_payload(appointment=appointment.id),
        format="json",
    )

    assert response.status_code == 400
    assert "appointment" in response.data["error"]["details"]


@pytest.mark.django_db
def test_patch_parcial_preserva_conteudo(api, patient):
    created = api.post(endpoint(patient), valid_payload(), format="json")
    response = api.patch(
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
def test_upload_valido_e_assinatura_invalida(api, patient, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    created = api.post(endpoint(patient), valid_payload(), format="json")
    url = f"/api/v1/records/clinical-evolutions/{created.data['id']}/attachments/"
    valid_png = SimpleUploadedFile(
        "evidencia.png",
        b"\x89PNG\r\n\x1a\n" + b"0" * 32,
        content_type="image/png",
    )
    invalid_png = SimpleUploadedFile(
        "falso.png",
        b"disguised executable content",
        content_type="image/png",
    )

    valid = api.post(url, {"file": valid_png}, format="multipart")
    invalid = api.post(url, {"file": invalid_png}, format="multipart")

    assert valid.status_code == 201
    assert invalid.status_code == 400
