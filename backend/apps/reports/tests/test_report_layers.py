from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase

from apps.patients.models import Patient
from apps.reports.selectors import patients_for_owner
from apps.reports.services.periods import resolve_period
from apps.users.models import User


class ReportLayerTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="report-owner@example.test",
            password="strong-password",
            full_name="Profissional Relatórios",
            role=User.Role.THERAPIST,
        )
        self.other_owner = User.objects.create_user(
            email="other-report-owner@example.test",
            password="strong-password",
            full_name="Outro Profissional",
            role=User.Role.THERAPIST,
        )
        self.patient = Patient.objects.create(full_name="Paciente do relatório", therapist=self.owner)
        Patient.objects.create(full_name="Paciente de outro tenant", therapist=self.other_owner)
        self.client.force_authenticate(self.owner)

    def test_patient_selector_does_not_leak_other_owner(self):
        self.assertQuerySetEqual(patients_for_owner(owner=self.owner), [self.patient])

    def test_custom_period_is_resolved_without_changing_contract(self):
        start, end = resolve_period({"start_date": "2026-01-01", "end_date": "2026-01-31"})
        self.assertEqual(start, date(2026, 1, 1))
        self.assertEqual(end, date(2026, 1, 31))

    def test_invalid_period_keeps_existing_api_error(self):
        response = self.client.get(
            "/api/v1/reports/patients/",
            {"start_date": "2026-02-01", "end_date": "2026-01-01"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {"detail": "Periodo invalido. Confira a data inicial e a data final informadas."},
        )

    def test_invalid_export_type_keeps_existing_api_error(self):
        response = self.client.get("/api/v1/reports/export/", {"type": "unknown"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "Tipo de relatorio invalido."})

    def test_patients_report_age_distribution(self):
        from django.utils import timezone
        today = timezone.localdate()
        # Set birth date of self.patient to correspond to exactly 8 years old
        self.patient.birth_date = date(today.year - 8, today.month, today.day)
        self.patient.save()

        # Create another patient for self.owner without birth date (Sem data)
        Patient.objects.create(
            full_name="Paciente sem data",
            therapist=self.owner,
            birth_date=None,
            organization=self.patient.organization,
        )

        response = self.client.get("/api/v1/reports/patients/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        age_distribution = response.data["charts"]["age_distribution"]

        # Verify age 8 bucket (6-10) is 1
        bucket_6_10 = next(item for item in age_distribution if item["label"] == "6-10")
        self.assertEqual(bucket_6_10["value"], 1)

        # Verify "Sem data" bucket is 1
        bucket_no_date = next(item for item in age_distribution if item["label"] == "Sem data")
        self.assertEqual(bucket_no_date["value"], 1)
