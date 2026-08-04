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

    def test_patients_report_performance_and_correctness(self):
        # Create patients with known ages
        Patient.objects.create(
            full_name="Paciente Jovem",
            therapist=self.owner,
            birth_date=date(2020, 1, 1),
        )
        Patient.objects.create(
            full_name="Paciente Adulto",
            therapist=self.owner,
            birth_date=date(1990, 1, 1),
        )
        Patient.objects.create(
            full_name="Paciente Sem Data",
            therapist=self.owner,
            birth_date=None,
        )

        from apps.reports.services import patients_report
        response_data = patients_report(
            user=self.owner,
            params={"start_date": "2026-01-01", "end_date": "2026-01-31"},
            organization=self.patient.organization,
        )

        age_distribution = response_data["charts"]["age_distribution"]

        # We have:
        # - "Paciente Jovem" (birth_date 2020-01-01) -> 6 years old (category "6-10")
        # - "Paciente Adulto" (birth_date 1990-01-01) -> 36 years old (category "36-45")
        # - "Paciente Sem Data" (birth_date None) -> "Sem data"
        # - self.patient (birth_date None) -> "Sem data"
        # So total "Sem data" = 2.

        category_6_10 = [b["value"] for b in age_distribution if b["label"] == "6-10"][0]
        category_36_45 = [b["value"] for b in age_distribution if b["label"] == "36-45"][0]
        sem_data_value = [b["value"] for b in age_distribution if b["label"] == "Sem data"][0]

        self.assertEqual(category_6_10, 1)
        self.assertEqual(category_36_45, 1)
        self.assertEqual(sem_data_value, 2)
