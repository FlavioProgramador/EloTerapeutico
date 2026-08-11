from __future__ import annotations

from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from apps.patients.models import Patient
from apps.records.checks import clinical_upload_scanner_check
from apps.records.services.clinical_document_scanning import (
    process_clinical_document_scan,
    register_document_scan_failure,
)
from apps.records.services.malware_scanning import MalwareScannerUnavailable
from apps.records.treatment_models import ClinicalDocument
from apps.users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def therapist():
    return User.objects.create_user(
        email="scan-owner@example.test",
        full_name="Scan Owner",
        password="safe-password-2026",
        role=User.Role.THERAPIST,
    )


@pytest.fixture
def patient(therapist):
    return Patient.objects.create(
        therapist=therapist,
        full_name="Paciente Scan",
        birth_date=date(1990, 1, 1),
        status=Patient.Status.ACTIVE,
    )


def _quarantined_document(patient, therapist) -> ClinicalDocument:
    uploaded = SimpleUploadedFile(
        "arquivo.pdf",
        b"%PDF-1.4\nconteudo de teste\n%%EOF",
        content_type="application/pdf",
    )
    return ClinicalDocument.objects.create(
        patient=patient,
        uploaded_by=therapist,
        quarantine_file=uploaded,
        file=None,
        original_name="arquivo.pdf",
        content_type="application/pdf",
        size_bytes=uploaded.size,
        checksum="a" * 64,
        scan_status=ClinicalDocument.ScanStatus.PENDING,
    )


@override_settings(
    CLINICAL_UPLOAD_SCANNER_BACKEND="mock_infected",
    CLINICAL_UPLOAD_SCANNER_ALLOW_MOCK=True,
)
def test_infected_file_is_rejected_and_removed_from_quarantine(patient, therapist):
    document = _quarantined_document(patient, therapist)

    result = process_clinical_document_scan(document.pk)

    document.refresh_from_db()
    assert result.status == ClinicalDocument.ScanStatus.INFECTED
    assert document.scan_status == ClinicalDocument.ScanStatus.INFECTED
    assert document.scan_error_code == "malware_detected"
    assert not document.file
    assert not document.quarantine_file
    assert document.is_downloadable is False


@override_settings(
    CLINICAL_UPLOAD_SCANNER_BACKEND="disabled",
    CLINICAL_UPLOAD_SCANNER_ALLOW_MOCK=False,
)
def test_scanner_unavailable_keeps_file_quarantined(patient, therapist):
    document = _quarantined_document(patient, therapist)

    with pytest.raises(MalwareScannerUnavailable) as exc_info:
        process_clinical_document_scan(document.pk)
    register_document_scan_failure(document.pk, exc_info.value)

    document.refresh_from_db()
    assert document.scan_status == ClinicalDocument.ScanStatus.FAILED
    assert document.scan_error_code == "scanner_unavailable"
    assert document.quarantine_file
    assert not document.file
    assert document.is_downloadable is False


def test_pending_document_cannot_be_downloaded(api_client, patient, therapist):
    document = _quarantined_document(patient, therapist)
    api_client.force_authenticate(therapist)

    response = api_client.get(
        reverse("clinical-document-download", kwargs={"pk": document.pk})
    )

    assert response.status_code == 423
    assert response.data["error"]["code"] == "CLINICAL_DOCUMENT_NOT_RELEASED"
    assert response.data["scan_status"] == ClinicalDocument.ScanStatus.PENDING


def test_file_replacement_cannot_bypass_quarantine(api_client, patient, therapist):
    document = _quarantined_document(patient, therapist)
    api_client.force_authenticate(therapist)
    replacement = SimpleUploadedFile(
        "substituto.pdf",
        b"%PDF-1.4\nsubstituto\n%%EOF",
        content_type="application/pdf",
    )

    response = api_client.patch(
        reverse("clinical-document-detail", kwargs={"pk": document.pk}),
        {"file": replacement},
        format="multipart",
    )

    assert response.status_code == 400
    document.refresh_from_db()
    assert document.scan_status == ClinicalDocument.ScanStatus.PENDING
    assert not document.file


@override_settings(
    SETTINGS_MODULE="config.settings.production",
    DEBUG=False,
    CLINICAL_UPLOAD_SCANNER_BACKEND="disabled",
    CLINICAL_UPLOAD_SCANNER_ALLOW_MOCK=False,
)
def test_production_check_rejects_disabled_scanner():
    errors = clinical_upload_scanner_check(None)

    assert {error.id for error in errors} == {"records.E001"}


@override_settings(
    SETTINGS_MODULE="config.settings.production",
    DEBUG=False,
    CLINICAL_UPLOAD_SCANNER_BACKEND="clamd",
    CLAMAV_HOST="",
)
def test_production_check_requires_clamav_host():
    errors = clinical_upload_scanner_check(None)

    assert {error.id for error in errors} == {"records.E003"}
