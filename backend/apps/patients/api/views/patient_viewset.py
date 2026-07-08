"""ViewSet canônico de pacientes sobre o contrato HTTP existente."""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.patients.exceptions import InvalidPatientState
from apps.patients.selectors.patients import patients_accessible_to
from apps.patients.services.lifecycle import deactivate as deactivate_patient
from apps.patients.services.lifecycle import restore as restore_patient
from .legacy_views import PatientViewSet as LegacyPatientViewSet


class PatientViewSet(LegacyPatientViewSet):
    def get_queryset(self):
        include_deleted = self.action == "restore"
        return patients_accessible_to(
            self.request.user,
            include_deleted=include_deleted,
        ).order_by("full_name")

    @action(detail=True, methods=["post"], url_path="deactivate")
    def deactivate(self, request, pk=None):
        try:
            deactivate_patient(self.get_object())
        except InvalidPatientState as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"detail": "Paciente desativado com sucesso."})

    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        try:
            restore_patient(self.get_object())
        except InvalidPatientState as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"detail": "Paciente restaurado com sucesso."})
