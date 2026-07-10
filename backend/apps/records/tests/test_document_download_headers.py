"""Testes dos cabeçalhos de proteção em downloads clínicos."""

from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.patients.models import Patient
from apps.records.treatment_models import ClinicalDocument
from apps.users.models import User


@pytest.mark.django_db
def test_clinical_document_download_disables_cache_and_mime_sniffing():
    therapist = User.objects.create_user(
        email="download-owner@teste.com",
        full_name="Download Owner",
        password="".join(["Test", "Pass", "2026!", "_download"]),
        role=User.Role.THERAPIST,
    )
    patient = Patient.objects.create(
        full_name="Paciente Download",
        cpf="52998224725",
        birth_date=date(1990, 1, 1),
        therapist=therapist,
    )
    document = ClinicalDocument.objects.create(
        patient=patient,
        category=ClinicalDocument.Category.PATIENT_FILE,
        file=SimpleUploadedFile(
            "documento.pdf",
            b"%PDF-1.4\nsecurity-test",
            content_type="application/pdf",
        ),
        original_name="documento.pdf",
        content_type="application/pdf",
        size_bytes=22,
        checksum="checksum-test",
        uploaded_by=therapist,
    )
    client = APIClient()
    client.force_authenticate(therapist)

    response = client.get(f"/api/v1/records/documents/{document.id}/download/")

    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store, max-age=0"
    assert response["Pragma"] == "no-cache"
    assert response["Expires"] == "0"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Cross-Origin-Resource-Policy"] == "same-origin"
