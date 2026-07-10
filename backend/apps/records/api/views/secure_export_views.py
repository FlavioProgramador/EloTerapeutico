"""Camada de autorização explícita para exportações de prontuário."""

from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from apps.records.api.serializers.clinical_serializers import ClinicalExportSerializer
from apps.records.api.views.clinical_views import (
    ClinicalExportDownloadView,
    ClinicalExportListCreateView,
    ClinicalExportRetryView,
    PatientRecordPdfView,
)
from apps.records.models import Evolution
from apps.records.services.evolution_security import has_explicit_records_permission
from apps.records.treatment_models import ClinicalExport
from core.audit import AuditLog, log_access


def _can_manage_foreign_export(user, export_obj: ClinicalExport) -> bool:
    if export_obj.created_by_id == user.id:
        return True
    return bool(
        getattr(user, "is_admin_role", False)
        and has_explicit_records_permission(user, "export_confidential_evolution")
    )


def _protect_file_response(response):
    response["Cache-Control"] = "private, no-store, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    response["X-Content-Type-Options"] = "nosniff"
    response["Cross-Origin-Resource-Policy"] = "same-origin"
    return response


class SecurePatientRecordPdfView(PatientRecordPdfView):
    """Impede que o papel administrativo ignore permissões clínicas explícitas."""

    def get(self, request, patient_id):
        patient = self.get_patient(patient_id)
        has_foreign_confidential = (
            Evolution.objects.filter(patient=patient, is_confidential=True)
            .exclude(created_by=request.user)
            .exists()
        )
        if has_foreign_confidential and not has_explicit_records_permission(
            request.user,
            "export_confidential_evolution",
        ):
            self.permission_denied(
                request,
                message="Você não tem permissão para exportar evoluções confidenciais deste paciente.",
            )
        return _protect_file_response(super().get(request, patient_id))


class SecureClinicalExportListCreateView(ClinicalExportListCreateView):
    """Lista apenas exportações próprias, salvo autorização administrativa explícita."""

    def get(self, request, patient_id):
        if request.user.is_secretary:
            self.permission_denied(
                request,
                message="Secretárias não possuem acesso a exportações clínicas.",
            )
        patient = self.get_patient(patient_id)
        queryset = ClinicalExport.objects.filter(patient=patient).order_by("-created_at")
        can_review_all = bool(
            request.user.is_admin_role
            and has_explicit_records_permission(request.user, "export_confidential_evolution")
        )
        if not can_review_all:
            queryset = queryset.filter(created_by=request.user)

        log_access(
            request,
            AuditLog.Action.VIEW,
            obj=patient,
            obj_repr=f"Lista de exportações do paciente #{patient.id}",
        )
        return Response(ClinicalExportSerializer(queryset, many=True).data)

    def post(self, request, patient_id):
        patient = self.get_patient(patient_id)
        has_foreign_confidential = (
            Evolution.objects.filter(patient=patient, is_confidential=True)
            .exclude(created_by=request.user)
            .exists()
        )
        if has_foreign_confidential and not has_explicit_records_permission(
            request.user,
            "export_confidential_evolution",
        ):
            self.permission_denied(
                request,
                message="Você não tem permissão para exportar evoluções confidenciais deste paciente.",
            )
        return super().post(request, patient_id)


class SecureClinicalExportRetryView(ClinicalExportRetryView):
    def post(self, request, pk):
        export_obj = get_object_or_404(ClinicalExport, pk=pk)
        self.get_patient(export_obj.patient_id)
        if not _can_manage_foreign_export(request.user, export_obj):
            self.permission_denied(
                request,
                message="Você não tem permissão para gerenciar esta exportação.",
            )
        return super().post(request, pk)


class SecureClinicalExportDownloadView(ClinicalExportDownloadView):
    def get(self, request, pk):
        export_obj = get_object_or_404(ClinicalExport, pk=pk)
        self.get_patient(export_obj.patient_id)
        if not _can_manage_foreign_export(request.user, export_obj):
            self.permission_denied(
                request,
                message="Você não tem permissão para baixar esta exportação.",
            )
        return _protect_file_response(super().get(request, pk))
