from __future__ import annotations

import csv
from io import StringIO
from typing import Any

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from weasyprint import HTML

from .services import (
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


class BaseReportView(APIView):
    permission_classes = [IsAuthenticated]

    def build_response(self, request, builder):
        try:
            return Response(builder(request.user, request.query_params))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


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

        try:
            payload = builder(request.user, request.query_params)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if export_format == "pdf":
            return self._pdf_response(report_type, payload)
        return self._csv_response(report_type, payload)

    def _csv_response(self, report_type: str, payload: dict[str, Any]) -> HttpResponse:
        output = StringIO()
        writer = csv.writer(output, delimiter=";")

        if report_type == "appointments":
            writer.writerow(["Data", "Horario", "Paciente", "Profissional", "Status", "Sala", "Convenio", "Valor"])
            for row in payload.get("table", {}).get("results", []):
                writer.writerow([row["date"], row["start_time"], row["patient"], row["professional"], row["status_display"], row["room"], row["insurance"], row["amount"]])
        elif report_type == "patients":
            writer.writerow(["Paciente", "Profissional", "Ultimo atendimento", "Proximo agendamento", "Dias sem consulta", "Status", "Contato"])
            for row in payload.get("risk", {}).get("results", []):
                writer.writerow([row["patient"], row["professional"], row["last_appointment"] or "", row["next_appointment"] or "", row["days_without_appointment"], row["status_display"], row["contact"] or ""])
        elif report_type == "financial":
            writer.writerow(["Data", "Tipo", "Descricao", "Paciente", "Categoria", "Convenio", "Valor", "Status", "Vencimento", "Pagamento"])
            for row in payload.get("transactions", {}).get("results", []):
                writer.writerow([row["date"], row["type_display"], row["description"], row["patient"], row["category_display"], row["insurance"], row["amount"], row["status_display"], row["due_date"] or "", row["paid_at"] or ""])
        else:
            writer.writerow(["Indicador", "Valor"])
            kpis = payload.get("kpis", {})
            for key, value in kpis.items():
                writer.writerow([key, value])

        response = HttpResponse("\ufeff" + output.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="relatorio-{report_type}.csv"'
        return response

    def _pdf_response(self, report_type: str, payload: dict[str, Any]) -> HttpResponse:
        period = payload.get("period", {})
        generated_at = timezone.localtime().strftime("%d/%m/%Y %H:%M")
        html = [
            "<html><head><meta charset='utf-8'>",
            "<style>body{font-family:Arial,sans-serif;color:#111827}table{width:100%;border-collapse:collapse;margin-top:16px}th,td{border:1px solid #d1d5db;padding:8px;font-size:12px;text-align:left}th{background:#f3f4f6}.metric{display:inline-block;margin:6px 10px 6px 0;padding:10px 12px;border:1px solid #d1d5db;border-radius:8px}</style>",
            "</head><body>",
            f"<h1>Relatorio {report_type}</h1>",
            f"<p>Periodo: {period.get('start_date')} ate {period.get('end_date')}<br>Gerado em: {generated_at}</p>",
        ]
        for key, value in payload.get("kpis", {}).items():
            html.append(f"<div class='metric'><strong>{key}</strong><br>{value}</div>")

        rows = []
        headers = []
        if report_type == "financial":
            headers = ["Indicador", "Valor"]
            dre = payload.get("dre", {})
            rows = list(dre.items())
        elif report_type == "appointments":
            headers = ["Data", "Paciente", "Status", "Sala", "Valor"]
            rows = [(r["date"], r["patient"], r["status_display"], r["room"], r["amount"]) for r in payload.get("table", {}).get("results", [])]
        elif report_type == "patients":
            headers = ["Paciente", "Profissional", "Dias sem consulta", "Status"]
            rows = [(r["patient"], r["professional"], r["days_without_appointment"], r["status_display"]) for r in payload.get("risk", {}).get("results", [])]

        if headers:
            html.append("<table><thead><tr>")
            html.extend(f"<th>{header}</th>" for header in headers)
            html.append("</tr></thead><tbody>")
            if rows:
                for row in rows:
                    html.append("<tr>")
                    html.extend(f"<td>{value}</td>" for value in row)
                    html.append("</tr>")
            else:
                html.append(f"<tr><td colspan='{len(headers)}'>Nenhum registro encontrado.</td></tr>")
            html.append("</tbody></table>")

        html.append("</body></html>")
        pdf = HTML(string="".join(html)).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="relatorio-{report_type}.pdf"'
        return response
