from datetime import date

import pytest
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.patients.models import Patient, PatientProfessional
from apps.records.models import Evolution
from apps.records.treatment_models import ClinicalDocument
from apps.users.models import User


@pytest.fixture
def workspace_context(db):
    owner = User.objects.create_user(
        email="workspace.owner@example.com",
        password="password",
        full_name="Terapeuta Responsável",
        role=User.Role.THERAPIST,
    )
    linked = User.objects.create_user(
        email="workspace.linked@example.com",
        password="password",
        full_name="Terapeuta Vinculado",
        role=User.Role.THERAPIST,
    )
    patient = Patient.objects.create(
        full_name="Paciente Workspace",
        cpf="12345678901",
        birth_date=date(1990, 1, 1),
        therapist=owner,
        status=Patient.Status.ACTIVE,
    )
    PatientProfessional.objects.create(
        patient=patient,
        professional=linked,
        is_active=True,
        assigned_by=owner,
    )
    client = APIClient()
    client.force_authenticate(linked)
    return owner, linked, patient, client


def create_document(*, patient, evolution, uploaded_by, name):
    content = b"%PDF-1.4\n%%EOF"
    return ClinicalDocument.objects.create(
        patient=patient,
        evolution=evolution,
        category=ClinicalDocument.Category.REPORT,
        file=SimpleUploadedFile(name, content, content_type="application/pdf"),
        original_name=name,
        content_type="application/pdf",
        size_bytes=len(content),
        checksum="workspace-checksum",
        uploaded_by=uploaded_by,
        scan_status=ClinicalDocument.ScanStatus.CLEAN,
    )


@pytest.mark.django_db
def test_workspace_oculta_documento_e_metadados_confidenciais_de_outro_autor(workspace_context):
    owner, _, patient, client = workspace_context
    evolution = Evolution.objects.create(
        patient=patient,
        created_by=owner,
        session_date=date.today(),
        content="Conteúdo confidencial",
        is_confidential=True,
    )
    confidential_document = create_document(
        patient=patient,
        evolution=evolution,
        uploaded_by=owner,
        name="confidencial.pdf",
    )

    response = client.get(f"/api/v1/records/patients/{patient.id}/workspace/")

    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.data["recent_documents"]}
    assert confidential_document.id not in returned_ids
    assert response.data["sessions_total"] == 0
    assert response.data["latest_evolution_id"] is None
    assert response.data["treatment_start"] == patient.created_at.date()
    assert response.data["last_update"] == patient.updated_at


@pytest.mark.django_db
def test_workspace_mostra_documento_e_metadados_com_permissao_explicita(workspace_context):
    owner, linked, patient, client = workspace_context
    evolution = Evolution.objects.create(
        patient=patient,
        created_by=owner,
        session_date=date.today(),
        content="Conteúdo confidencial",
        is_confidential=True,
    )
    confidential_document = create_document(
        patient=patient,
        evolution=evolution,
        uploaded_by=owner,
        name="confidencial-autorizado.pdf",
    )
    permission = Permission.objects.get(
        codename="view_confidential_evolution",
        content_type__app_label="records",
    )
    linked.user_permissions.add(permission)
    linked.refresh_from_db()
    client.force_authenticate(linked)

    response = client.get(f"/api/v1/records/patients/{patient.id}/workspace/")

    assert response.status_code == 200
    returned_ids = {item["id"] for item in response.data["recent_documents"]}
    assert confidential_document.id in returned_ids
    assert response.data["sessions_total"] == 1
    assert response.data["latest_evolution_id"] == evolution.id
    assert response.data["treatment_start"] == evolution.session_date
    assert response.data["last_update"] == evolution.updated_at
