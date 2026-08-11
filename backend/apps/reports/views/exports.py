"""Exportação CSV dos relatórios disponíveis."""

import csv
from io import StringIO
from typing import Any

from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.services.tenant_context import ensure_request_organization
from apps.reports.permissions import CanExportReports
from apps.reports.services import (
    appointments_report,
    financial_report,
    online_scheduling_report,
    patients_report,
)
from apps.reports.views.reports import INVALID_PERIOD_RESPONSE

REPORT_BUILDERS = {
    "appointments": appointments_report,
    "patients": patients_report,
    "financial": financial_report,
    "online-scheduling": online_scheduling_report,
}
PDF_UNAVAILABLE_RESPONSE = {
    "detail": "Exportacao em PDF temporariamente indisponivel. Use CSV neste momento."
}


class ReportExportView(APIView):
    permission_classes = [IsAuthenticated, CanExportReports]

    def get(self, request):
        organization, _ = ensure_request_organization(
            request=request,
            required=True,
        )
        report_type = request.query_params.get("type") or "appointments"
        export_format = request.query_params.get("format") or "csv"
        builder = REPORT_BUILDERS.get(report_type)
        if not builder:
            return Response(
                {"detail": "Tipo de relatorio invalido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if export_format not in {"csv", "pdf"}:
            return Response(
                {"detail": "Formato de exportacao invalido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if export_format == "pdf":
            return Response(
                PDF_UNAVAILABLE_RESPONSE,
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            payload = builder(
                request.user,
                request.query_params,
                organization=organization,
            )
        except ValueError:
            return Response(
                INVALID_PERIOD_RESPONSE,
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self._csv_response(report_type, payload)

    def _csv_response(
        self,
        report_type: str,
        payload: dict[str, Any],
    ) -> HttpResponse:
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

        response = HttpResponse(
            "\ufeff" + output.getvalue(),
            content_type="text/csv; charset=utf-8",
        )
        response["Content-Disposition"] = (
            f'attachment; filename="relatorio-{report_type}.csv"'
        )
        response["Cache-Control"] = "private, no-store, max-age=0"
        response["X-Content-Type-Options"] = "nosniff"
        return response
