# mypy: ignore-errors
import csv
from io import StringIO

from django.http import HttpResponse
from rest_framework.decorators import action

from apps.audit.models import AuditLog
from apps.audit.services import log_access
from apps.organizations.permissions import require_capability
from apps.organizations.services.tenant_context import ensure_request_organization


class PatientExportActions:
    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request):
        _, membership = ensure_request_organization(request=request, required=True)
        require_capability(membership, "patients.view")

        queryset = self.filter_queryset(self.get_queryset()).order_by("full_name")
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "Nome",
                "CPF mascarado",
                "E-mail",
                "Telefone",
                "Status",
                "Terapeuta",
                "Modalidade",
                "Forma de atendimento",
            ]
        )
        for patient in queryset.iterator():
            writer.writerow(
                [
                    patient.display_name,
                    patient.masked_cpf,
                    patient.email,
                    patient.phone,
                    patient.get_status_display(),
                    patient.therapist.full_name,
                    patient.get_modality_display(),
                    patient.get_payer_type_display(),
                ]
            )
        log_access(
            request,
            AuditLog.Action.EXPORT,
            obj=None,
            obj_repr="Exportação autorizada da listagem de pacientes",
        )
        response = HttpResponse(
            buffer.getvalue(),
            content_type="text/csv; charset=utf-8",
        )
        response["Content-Disposition"] = 'attachment; filename="pacientes.csv"'
        return response
