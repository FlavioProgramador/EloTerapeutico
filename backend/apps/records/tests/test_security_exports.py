import pytest
from django.core.files.base import ContentFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.patients.models import Patient, PatientProfessional
from apps.records.treatment_models import ClinicalExport
from apps.users.models import User


@pytest.fixture
def therapist_a(db):
    return User.objects.create_user(
        email="therapist_a@example.com",
        password="password123",
        full_name="Therapist A",
        role=User.Role.THERAPIST,
    )


@pytest.fixture
def therapist_b(db):
    return User.objects.create_user(
        email="therapist_b@example.com",
        password="password123",
        full_name="Therapist B",
        role=User.Role.THERAPIST,
    )


@pytest.fixture
def patient(therapist_a):
    return Patient.objects.create(
        full_name="Patient Test",
        therapist=therapist_a,
        status=Patient.Status.ACTIVE,
    )


@pytest.fixture
def linked_therapist_b(patient, therapist_b, therapist_a):
    return PatientProfessional.objects.create(
        patient=patient, professional=therapist_b, is_active=True, assigned_by=therapist_a
    )


@pytest.mark.django_db
class TestClinicalExportSecurity:
    def test_linked_therapist_cannot_list_others_exports(self, therapist_a, therapist_b, patient, linked_therapist_b):
        # Therapist A creates an export
        export_a = ClinicalExport.objects.create(
            patient=patient,
            export_type="pdf",
            filename="export_a.pdf",
            created_by=therapist_a,
            status=ClinicalExport.Status.COMPLETED,
        )

        client = APIClient()
        client.force_authenticate(user=therapist_b)

        url = reverse("patient-exports", kwargs={"patient_id": patient.id})
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        export_ids = [e["id"] for e in response.data]
        assert export_a.id not in export_ids

    def test_linked_therapist_cannot_download_others_exports(
        self, therapist_a, therapist_b, patient, linked_therapist_b
    ):
        # Therapist A creates an export with a dummy file
        export_a = ClinicalExport.objects.create(
            patient=patient,
            export_type="pdf",
            filename="export_a.pdf",
            created_by=therapist_a,
            status=ClinicalExport.Status.COMPLETED,
        )
        export_a.file.save("export_a.pdf", ContentFile(b"dummy content"))

        client = APIClient()
        client.force_authenticate(user=therapist_b)

        url = reverse("export-download", kwargs={"pk": export_a.id})
        response = client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_linked_therapist_cannot_retry_others_exports(self, therapist_a, therapist_b, patient, linked_therapist_b):
        # Therapist A creates a failed export
        export_a = ClinicalExport.objects.create(
            patient=patient,
            export_type="pdf",
            filename="export_a.pdf",
            created_by=therapist_a,
            status=ClinicalExport.Status.FAILED,
        )

        client = APIClient()
        client.force_authenticate(user=therapist_b)

        url = reverse("export-retry", kwargs={"pk": export_a.id})
        response = client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_owner_can_access_own_exports(self, therapist_a, patient):
        export_a = ClinicalExport.objects.create(
            patient=patient,
            export_type="pdf",
            filename="export_a.pdf",
            created_by=therapist_a,
            status=ClinicalExport.Status.COMPLETED,
        )
        export_a.file.save("export_a.pdf", ContentFile(b"dummy content"))

        client = APIClient()
        client.force_authenticate(user=therapist_a)

        # Can list
        url_list = reverse("patient-exports", kwargs={"patient_id": patient.id})
        assert export_a.id in [e["id"] for e in client.get(url_list).data]

        # Can download
        url_dl = reverse("export-download", kwargs={"pk": export_a.id})
        assert client.get(url_dl).status_code == status.HTTP_200_OK

    def test_secretary_cannot_access_clinical_exports(self, therapist_a, patient):
        secretary = User.objects.create_user(
            email="secretary_test@example.com",
            password="password123",
            full_name="Secretary",
            role=User.Role.SECRETARY,
        )
        export_a = ClinicalExport.objects.create(
            patient=patient,
            export_type="pdf",
            filename="export_a.pdf",
            created_by=therapist_a,
            status=ClinicalExport.Status.COMPLETED,
        )

        client = APIClient()
        client.force_authenticate(user=secretary)

        # Cannot list
        url_list = reverse("patient-exports", kwargs={"patient_id": patient.id})
        assert client.get(url_list).status_code == status.HTTP_403_FORBIDDEN

        # Cannot download
        url_dl = reverse("export-download", kwargs={"pk": export_a.id})
        assert client.get(url_dl).status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_access_all_exports(self, therapist_a, patient):
        admin = User.objects.create_user(
            email="admin_test@example.com",
            password="password123",
            full_name="Admin",
            role=User.Role.ADMIN,
        )
        export_a = ClinicalExport.objects.create(
            patient=patient,
            export_type="pdf",
            filename="export_a.pdf",
            created_by=therapist_a,
            status=ClinicalExport.Status.COMPLETED,
        )
        export_a.file.save("export_a.pdf", ContentFile(b"dummy content"))

        client = APIClient()
        client.force_authenticate(user=admin)

        # Can list
        url_list = reverse("patient-exports", kwargs={"patient_id": patient.id})
        assert export_a.id in [e["id"] for e in client.get(url_list).data]

        # Can download
        url_dl = reverse("export-download", kwargs={"pk": export_a.id})
        assert client.get(url_dl).status_code == status.HTTP_200_OK
