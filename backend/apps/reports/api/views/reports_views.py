from __future__ import annotations

import csv
from io import StringIO
from typing import Any

from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.reports.services.core_services import (
    appointments_report,
    financial_report,
    online_scheduling_report,
    patients_report,
)

REPORT_BUILDERS = {
    "appointments": appointments_report,
    "patients": patients_report,
    "financial": financial_report,
    "online-scheduling": online_scheduling_report,
}

INVALID_PERIOD_RESPONSE = {"detail": "Periodo invalido. Confira a data inicial e a data final informadas."}
PDF_UNAVAILABLE_RESPONSE = {"detail": "Exportacao em PDF temporariamente indisponivel. Use CSV neste momento."}


class BaseReportView(APIView):
    permission_classes = [IsAuthenticated]

    def build_response(self, request, builder):
        try:
            return Response(builder(request.user, request.query_params))
        except ValueError:
            return Response(INVALID_PERIOD_RESPONSE, status=status.HTTP_400_BAD_REQUEST)


class AppointmentsReportView(BaseReportView):
    def get(self, request):
        return self.build_response(request, appointments_report)


class PatientsReportView(BaseReportView):
    def get(self, request):
        return self.build_response(request, patients_report)


class FinancialReportView(BaseReportView):
    def get(self, request):
        return self.build_response(request, financial_report)


class OnlineSchedulingReportView(BaseReportView):
    def get(self, request):
        return self.build_response(request, online_scheduling_report)


class ReportExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        report_type = request.query_params.get("type") or "appointments"
        export_format = request.query_params.get("format") or "csv"
        builder = REPORT_BUILDERS.get(report_type)
        if not builder:
            return Response({"detail": "Tipo de relatorio invalido."}, status=status.HTTP_400_BAD_REQUEST)
        if export_format not in {"csv", "pdf"}:
            return Response({"detail": "Formato de exportacao invalido."}, status=status.HTTP_400_BAD_REQUEST)
        if export_format == "pdf":
            return Response(PDF_UNAVAILABLE_RESPONSE, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            payload = builder(request.user, request.query_params)
        except ValueError:
            return Response(INVALID_PERIOD_RESPONSE, status=status.HTTP_400_BAD_REQUEST)

        return self._csv_response(report_type, payload)

    def _csv_response(self, report_type: str, payload: dict[str, Any]) -> HttpResponse:
        output = StringIO()
        writer = csv.writer(output, delimiter=";")

        if report_type == "appointments":
            writer.writerow(
                [
                    "Data",
                    "Horario",
                    "Paciente",
                    "Profissional",
                    "Status",
                    "Sala",
                    "Convenio",
                    "Valor",
                ]
            )
            for row in payload.get("table", {}).get("results", []):
                writer.writerow(
                    [
                        row["date"],
                        row["start_time"],
                        row["patient"],
                        row["professional"],
                        row["status_display"],
                        row["room"],
                        row["insurance"],
                        row["amount"],
                    ]
                )
        elif report_type == "patients":
            writer.writerow(
                [
                    "Paciente",
                    "Profissional",
                    "Ultimo atendimento",
                    "Proximo agendamento",
                    "Dias sem consulta",
                    "Status",
                    "Contato",
                ]
            )
            for row in payload.get("risk", {}).get("results", []):
                writer.writerow(
                    [
                        row["patient"],
                        row["professional"],
                        row["last_appointment"] or "",
                        row["next_appointment"] or "",
                        row["days_without_appointment"],
                        row["status_display"],
                        row["contact"] or "",
                    ]
                )
        elif report_type == "financial":
            writer.writerow(
                [
                    "Data",
                    "Tipo",
                    "Descricao",
                    "Paciente",
                    "Categoria",
                    "Convenio",
                    "Valor",
                    "Status",
                    "Vencimento",
                    "Pagamento",
                ]
            )
            for row in payload.get("transactions", {}).get("results", []):
                writer.writerow(
                    [
                        row["date"],
                        row["type_display"],
                        row["description"],
                        row["patient"],
                        row["category_display"],
                        row["insurance"],
                        row["amount"],
                        row["status_display"],
                        row["due_date"] or "",
                        row["paid_at"] or "",
                    ]
                )
        else:
            writer.writerow(["Indicador", "Valor"])
            kpis = payload.get("kpis", {})
            for key, value in kpis.items():
                writer.writerow([key, value])

        response = HttpResponse("\ufeff" + output.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="relatorio-{report_type}.csv"'
        return response
