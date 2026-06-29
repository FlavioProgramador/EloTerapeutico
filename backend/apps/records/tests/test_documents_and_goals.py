from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.records.models import Evolution
from apps.records.treatment_models import ClinicalDocument, TreatmentGoal
from apps.users.models import User


@pytest.fixture
def context(db):
    therapist = User.objects.create_user(
        email="owner@example.com",
        password="safe-password",
        full_name="Terapeuta",
        role=User.Role.THERAPIST,
    )
    patient = Patient.objects.create(
        full_name="Paciente",
        cpf="52998224725",
        birth_date=date(1995, 4, 12),
        therapist=therapist,
        status=Patient.Status.ACTIVE,
    )
    client = APIClient()
    client.force_authenticate(therapist)
    return client, therapist, patient


@pytest.mark.django_db
def test_documento_rejeita_extensao_invalida(context):
    client, _, patient = context
    uploaded = SimpleUploadedFile(
        "arquivo.exe",
        b"invalid",
        content_type="application/octet-stream",
    )

    response = client.post(
        f"/api/v1/records/patients/{patient.id}/documents/",
        {"file": uploaded, "category": "other"},
        format="multipart",
    )

    assert response.status_code == 400
    assert ClinicalDocument.objects.count() == 0


@pytest.mark.django_db
def test_documento_valido_nao_expoe_url_publica(context):
    client, therapist, patient = context
    uploaded = SimpleUploadedFile(
        "termo.pdf",
        b"%PDF-1.4 test",
        content_type="application/pdf",
    )

    response = client.post(
        f"/api/v1/records/patients/{patient.id}/documents/",
        {"file": uploaded, "category": "consent"},
        format="multipart",
    )

    assert response.status_code == 201
    assert "file" not in response.data
    assert response.data["download_url"].endswith(
        f"/api/v1/records/documents/{response.data['id']}/download/"
    )
    assert response.data["status"] == "available"
    assert response.data["status_display"] == "Disponível"
    assert response.data["uploaded_by_name"] == therapist.full_name


@pytest.mark.django_db
def test_meta_rejeita_evolucao_de_outro_paciente(context):
    client, therapist, patient = context
    other_patient = Patient.objects.create(
        full_name="Outro Paciente",
        cpf="11144477735",
        birth_date=date(1990, 1, 1),
        therapist=therapist,
        status=Patient.Status.ACTIVE,
    )
    evolution = Evolution.objects.create(
        patient=other_patient,
        created_by=therapist,
        session_date=date(2026, 6, 28),
        content="Registro de teste",
    )

    response = client.post(
        f"/api/v1/records/patients/{patient.id}/goals/",
        {
            "title": "Meta de teste",
            "priority": "medium",
            "status": "active",
            "progress": 10,
            "start_date": "2026-06-29",
            "evolutions": [evolution.id],
        },
        format="json",
    )

    assert response.status_code == 400
    assert TreatmentGoal.objects.count() == 0


@pytest.mark.django_db
def test_meta_expoe_profissional_responsavel(context):
    client, therapist, patient = context

    response = client.post(
        f"/api/v1/records/patients/{patient.id}/goals/",
        {
            "title": "Reduzir ansiedade social",
            "priority": "high",
            "status": "active",
            "progress": 25,
            "start_date": "2026-06-29",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["created_by_name"] == therapist.full_name
