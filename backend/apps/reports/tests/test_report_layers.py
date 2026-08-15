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
        from apps.reports.services.patient_reports import patients_report

        today = timezone.localdate()
        # Create patients in different age buckets
        Patient.objects.create(
            full_name="Paciente Criança",
            therapist=self.owner,
            birth_date=date(today.year - 3, today.month, today.day),
        )
        Patient.objects.create(
            full_name="Paciente Adulto",
            therapist=self.owner,
            birth_date=date(today.year - 30, today.month, today.day),
        )

        result = patients_report(user=self.owner, params={})
        age_dist = {item["label"]: item["value"] for item in result["charts"]["age_distribution"]}

        self.assertEqual(age_dist["0-5"], 1)
        self.assertEqual(age_dist["26-35"], 1)
        self.assertEqual(age_dist["Sem data"], 1)  # self.patient has no birth_date
