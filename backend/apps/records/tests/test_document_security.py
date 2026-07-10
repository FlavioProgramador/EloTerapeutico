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
def api_clients(db):
    t1 = User.objects.create_user(
        email="t1@example.com",
        password="password",
        full_name="Terapeuta 1",
        role=User.Role.THERAPIST,
    )
    t2 = User.objects.create_user(
        email="t2@example.com",
        password="password",
        full_name="Terapeuta 2",
        role=User.Role.THERAPIST,
    )

    patient = Patient.objects.create(
        full_name="Paciente Compartilhado",
        cpf="12345678901",
        birth_date=date(1990, 1, 1),
        therapist=t1,
    )

    PatientProfessional.objects.create(
        patient=patient,
        professional=t2,
        is_active=True,
        assigned_by=t1,
    )

    c1 = APIClient()
    c1.force_authenticate(t1)

    c2 = APIClient()
    c2.force_authenticate(t2)

    admin = User.objects.create_superuser(
        email="admin@example.com",
        password="password",
        full_name="Admin",
    )
    admin.role = User.Role.ADMIN
    admin.save()

    ca = APIClient()
    ca.force_authenticate(admin)

    return {
        "t1": t1,
        "t2": t2,
        "admin": admin,
        "c1": c1,
        "c2": c2,
        "ca": ca,
        "patient": patient,
    }


def create_document(*, patient, uploaded_by, evolution=None, name="relatorio.pdf"):
    content = b"%PDF-1.4\n%%EOF"
    return ClinicalDocument.objects.create(
        patient=patient,
        evolution=evolution,
        category=ClinicalDocument.Category.REPORT,
        file=SimpleUploadedFile(name, content, content_type="application/pdf"),
        original_name=name,
        size_bytes=len(content),
        checksum="abc",
        uploaded_by=uploaded_by,
    )


@pytest.mark.django_db
def test_terapeuta_sem_acesso_nao_ve_documento_de_evolucao_confidencial(api_clients):
    c2 = api_clients["c2"]
    t1 = api_clients["t1"]
    patient = api_clients["patient"]

    evolution = Evolution.objects.create(
        patient=patient,
        created_by=t1,
        session_date=date.today(),
        content="Conteúdo confidencial",
        is_confidential=True,
    )
    document = create_document(patient=patient, uploaded_by=t1, evolution=evolution)

    response = c2.get(f"/api/v1/records/patients/{patient.id}/documents/")

    assert response.status_code == 200
    document_ids = [item["id"] for item in response.data]
    assert document.id not in document_ids


@pytest.mark.django_db
def test_terapeuta_sem_acesso_nao_baixa_documento_de_evolucao_confidencial(api_clients):
    c2 = api_clients["c2"]
    t1 = api_clients["t1"]
    patient = api_clients["patient"]

    evolution = Evolution.objects.create(
        patient=patient,
        created_by=t1,
        session_date=date.today(),
        content="Conteúdo confidencial",
        is_confidential=True,
    )
    document = create_document(patient=patient, uploaded_by=t1, evolution=evolution)

    response = c2.get(f"/api/v1/records/documents/{document.id}/download/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_superusuario_precisa_de_permissao_explicita_para_documento_confidencial(api_clients):
    client = api_clients["ca"]
    admin = api_clients["admin"]
    t1 = api_clients["t1"]
    patient = api_clients["patient"]

    evolution = Evolution.objects.create(
        patient=patient,
        created_by=t1,
        session_date=date.today(),
        content="Confidencial",
        is_confidential=True,
    )
    document = create_document(patient=patient, uploaded_by=t1, evolution=evolution)
    download_url = f"/api/v1/records/documents/{document.id}/download/"

    assert client.get(download_url).status_code == 403

    permission = Permission.objects.get(
        codename="view_confidential_evolution",
        content_type__app_label="records",
    )
    admin.user_permissions.add(permission)
    admin.refresh_from_db()
    client.force_authenticate(admin)

    assert client.get(download_url).status_code == 200


@pytest.mark.django_db
def test_documento_sem_evolucao_acessivel_a_profissionais_compartilhados(api_clients):
    c2 = api_clients["c2"]
    t1 = api_clients["t1"]
    patient = api_clients["patient"]
    document = create_document(patient=patient, uploaded_by=t1, name="doc.pdf")

    response = c2.get(f"/api/v1/records/documents/{document.id}/download/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_download_clinico_impede_cache_e_sniffing(api_clients):
    c1 = api_clients["c1"]
    t1 = api_clients["t1"]
    patient = api_clients["patient"]
    document = create_document(patient=patient, uploaded_by=t1, name="protegido.pdf")

    response = c1.get(f"/api/v1/records/documents/{document.id}/download/")

    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store, max-age=0"
    assert response["Pragma"] == "no-cache"
    assert response["Expires"] == "0"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Cross-Origin-Resource-Policy"] == "same-origin"


@pytest.mark.django_db
def test_usuario_nao_autenticado_rejeitado(api_clients):
    patient = api_clients["patient"]
    t1 = api_clients["t1"]
    document = create_document(patient=patient, uploaded_by=t1, name="doc.pdf")

    client = APIClient()
    response = client.get(f"/api/v1/records/documents/{document.id}/download/")

    assert response.status_code == 401
