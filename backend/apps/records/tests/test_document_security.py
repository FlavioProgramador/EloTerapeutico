import pytest
from datetime import date
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from apps.users.models import User
from apps.patients.models import Patient, PatientProfessional
from apps.records.models import Evolution
from apps.records.treatment_models import ClinicalDocument

@pytest.fixture
def api_clients(db):
    # Terapeuta 1 (Dono do paciente)
    t1 = User.objects.create_user(
        email="t1@example.com",
        password="password",
        full_name="Terapeuta 1",
        role=User.Role.THERAPIST,
    )
    # Terapeuta 2 (Com acesso compartilhado)
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

    # Compartilha o paciente com t2
    PatientProfessional.objects.create(
        patient=patient,
        professional=t2,
        is_active=True,
        assigned_by=t1
    )

    c1 = APIClient()
    c1.force_authenticate(t1)

    c2 = APIClient()
    c2.force_authenticate(t2)

    # Admin
    admin = User.objects.create_superuser(
        email="admin@example.com",
        password="password",
        full_name="Admin"
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
        "patient": patient
    }

@pytest.mark.django_db
def test_terapeuta_sem_acesso_nao_ve_documento_de_evolucao_confidencial(api_clients):
    c1 = api_clients["c1"]
    c2 = api_clients["c2"]
    t1 = api_clients["t1"]
    patient = api_clients["patient"]

    # T1 cria evolução confidencial
    evolution = Evolution.objects.create(
        patient=patient,
        created_by=t1,
        session_date=date.today(),
        content="Conteúdo confidencial",
        is_confidential=True
    )

    # T1 anexa documento à evolução
    doc = ClinicalDocument.objects.create(
        patient=patient,
        evolution=evolution,
        category=ClinicalDocument.Category.REPORT,
        file=SimpleUploadedFile("relatorio.pdf", b"pdf content", content_type="application/pdf"),
        original_name="relatorio.pdf",
        size_bytes=11,
        checksum="abc",
        uploaded_by=t1
    )

    # T2 lista documentos do paciente
    response = c2.get(f"/api/v1/records/patients/{patient.id}/documents/")
    assert response.status_code == 200

    # ATENÇÃO: Atualmente isso falha (T2 consegue ver o documento)
    # O objetivo da correção é fazer com que T2 NÃO veja o documento.
    doc_ids = [d["id"] for d in response.data]
    assert doc.id not in doc_ids, "Terapeuta sem acesso não deveria ver documento de evolução confidencial"

@pytest.mark.django_db
def test_terapeuta_sem_acesso_nao_baixa_documento_de_evolucao_confidencial(api_clients):
    c1 = api_clients["c1"]
    c2 = api_clients["c2"]
    t1 = api_clients["t1"]
    patient = api_clients["patient"]

    # T1 cria evolução confidencial
    evolution = Evolution.objects.create(
        patient=patient,
        created_by=t1,
        session_date=date.today(),
        content="Conteúdo confidencial",
        is_confidential=True
    )

    # T1 anexa documento à evolução
    doc = ClinicalDocument.objects.create(
        patient=patient,
        evolution=evolution,
        category=ClinicalDocument.Category.REPORT,
        file=SimpleUploadedFile("relatorio.pdf", b"pdf content", content_type="application/pdf"),
        original_name="relatorio.pdf",
        size_bytes=11,
        checksum="abc",
        uploaded_by=t1
    )

    # T2 tenta baixar o documento diretamente pelo ID
    response = c2.get(f"/api/v1/records/documents/{doc.id}/download/")

    # ATENÇÃO: Atualmente isso retorna 200. Deveria retornar 403.
    assert response.status_code == 403, "Terapeuta sem acesso não deveria baixar documento de evolução confidencial"

@pytest.mark.django_db
def test_admin_acessa_documento_de_evolucao_confidencial(api_clients):
    ca = api_clients["ca"]
    t1 = api_clients["t1"]
    patient = api_clients["patient"]

    evolution = Evolution.objects.create(
        patient=patient,
        created_by=t1,
        session_date=date.today(),
        content="Confidencial",
        is_confidential=True
    )
    doc = ClinicalDocument.objects.create(
        patient=patient,
        evolution=evolution,
        category=ClinicalDocument.Category.REPORT,
        file=SimpleUploadedFile("relatorio.pdf", b"pdf content", content_type="application/pdf"),
        original_name="relatorio.pdf",
        size_bytes=11,
        checksum="abc",
        uploaded_by=t1
    )

    response = ca.get(f"/api/v1/records/documents/{doc.id}/download/")
    assert response.status_code == 200

@pytest.mark.django_db
def test_documento_sem_evolucao_acessivel_a_profissionais_compartilhados(api_clients):
    c2 = api_clients["c2"]
    t1 = api_clients["t1"]
    patient = api_clients["patient"]

    doc = ClinicalDocument.objects.create(
        patient=patient,
        category=ClinicalDocument.Category.PATIENT_FILE,
        file=SimpleUploadedFile("doc.pdf", b"content", content_type="application/pdf"),
        original_name="doc.pdf",
        size_bytes=7,
        checksum="def",
        uploaded_by=t1
    )

    response = c2.get(f"/api/v1/records/documents/{doc.id}/download/")
    assert response.status_code == 200

@pytest.mark.django_db
def test_usuario_nao_autenticado_rejeitado(api_clients):
    patient = api_clients["patient"]
    t1 = api_clients["t1"]
    doc = ClinicalDocument.objects.create(
        patient=patient,
        category=ClinicalDocument.Category.PATIENT_FILE,
        file=SimpleUploadedFile("doc.pdf", b"content", content_type="application/pdf"),
        original_name="doc.pdf",
        size_bytes=7,
        checksum="def",
        uploaded_by=t1
    )

    client = APIClient()
    response = client.get(f"/api/v1/records/documents/{doc.id}/download/")
    assert response.status_code == 401
