from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.records.services.document_upload_security import validate_clinical_document_upload
from apps.users.models import User


def build_docx() -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            "<?xml version='1.0'?><Types xmlns='http://schemas.openxmlformats.org/package/2006/content-types'/>",
        )
        archive.writestr(
            "word/document.xml",
            "<?xml version='1.0'?><document xmlns='http://schemas.openxmlformats.org/wordprocessingml/2006/main'/>",
        )
    return output.getvalue()


@pytest.mark.django_db
def test_endpoint_rejeita_pdf_com_conteudo_executavel_disfarcado():
    therapist = User.objects.create_user(
        email="upload.security@example.com",
        password="password",
        full_name="Terapeuta Upload",
        role=User.Role.THERAPIST,
    )
    patient = Patient.objects.create(
        full_name="Paciente Upload",
        therapist=therapist,
        status=Patient.Status.ACTIVE,
    )
    client = APIClient()
    client.force_authenticate(therapist)
    fake_pdf = SimpleUploadedFile(
        "laudo.pdf",
        b"MZfake-windows-executable",
        content_type="application/pdf",
    )

    response = client.post(
        f"/api/v1/records/patients/{patient.id}/documents/",
        {"category": "report", "file": fake_pdf},
        format="multipart",
    )

    assert response.status_code == 400
    assert not patient.clinical_documents.exists()


@pytest.mark.django_db
def test_endpoint_aceita_pdf_com_assinatura_valida():
    therapist = User.objects.create_user(
        email="upload.valid@example.com",
        password="password",
        full_name="Terapeuta Upload Válido",
        role=User.Role.THERAPIST,
    )
    patient = Patient.objects.create(
        full_name="Paciente Upload Válido",
        therapist=therapist,
        status=Patient.Status.ACTIVE,
    )
    client = APIClient()
    client.force_authenticate(therapist)
    valid_pdf = SimpleUploadedFile(
        "laudo.pdf",
        b"%PDF-1.4\n%%EOF",
        content_type="application/pdf",
    )

    response = client.post(
        f"/api/v1/records/patients/{patient.id}/documents/",
        {"category": "report", "file": valid_pdf},
        format="multipart",
    )

    assert response.status_code == 201
    assert patient.clinical_documents.filter(original_name="laudo.pdf").exists()


def test_validador_rejeita_docx_que_e_apenas_um_zip_generico():
    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("arquivo.txt", "conteúdo")
    fake_docx = SimpleUploadedFile(
        "documento.docx",
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    with pytest.raises(ValidationError, match="estrutura DOCX válida"):
        validate_clinical_document_upload(fake_docx)


def test_validador_aceita_estrutura_docx_minima_valida():
    valid_docx = SimpleUploadedFile(
        "documento.docx",
        build_docx(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert validate_clinical_document_upload(valid_docx) is valid_docx
    assert valid_docx.tell() == 0


def test_validador_rejeita_texto_com_dados_binarios():
    binary_text = SimpleUploadedFile(
        "observacao.txt",
        b"texto\x00binario",
        content_type="text/plain",
    )

    with pytest.raises(ValidationError, match="dados binários"):
        validate_clinical_document_upload(binary_text)
