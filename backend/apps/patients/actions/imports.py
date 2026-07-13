"""Ação HTTP de importação de pacientes."""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.services.access_logging import AuditLog, log_access

from ..services.imports import PatientImportError, import_patients_from_csv


class PatientImportActions:
    @action(detail=False, methods=["post"], url_path="import-csv")
    def import_csv(self, request):
        if not request.user.is_therapist:
            return Response(
                {"detail": "Operação permitida somente para terapeutas."},
                status=status.HTTP_403_FORBIDDEN,
            )
        uploaded = request.FILES.get("file")
        if uploaded is None:
            return Response(
                {"detail": "Envie um arquivo CSV."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = import_patients_from_csv(
                uploaded_file=uploaded,
                therapist=request.user,
                confirm=str(request.data.get("confirm", "false")).lower() == "true",
            )
        except PatientImportError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if result.imported:
            log_access(
                request,
                AuditLog.Action.CREATE,
                obj_repr=f"Importação de {result.imported} pacientes",
            )
        response_status = status.HTTP_201_CREATED if result.imported else status.HTTP_200_OK
        return Response(result.as_dict(), status=response_status)
