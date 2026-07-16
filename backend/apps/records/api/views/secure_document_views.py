"""Views de documentos clínicos com proteção de evoluções confidenciais."""

from __future__ import annotations

from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services.access_logging import AuditLog, log_access
from apps.records.api.serializers.secure_document_serializers import SecureClinicalDocumentSerializer
from apps.records.api.views.clinical_views import ClinicalPatientMixin
from apps.records.services.clinical_document_scanning import create_quarantined_document
from apps.records.services.evolution_security import (
    can_view_confidential_evolution,
    has_explicit_records_permission,
    sanitize_original_filename,
)
from apps.records.treatment_models import ClinicalDocument


class SecureClinicalDocumentMixin(ClinicalPatientMixin):
    def get_document(self, pk):
        document = get_object_or_404(
            ClinicalDocument.objects.select_related(
                "patient",
                "patient__therapist",
                "evolution",
                "evolution__created_by",
            ),
            pk=pk,
            deleted_at__isnull=True,
        )
        self.get_patient(document.patient_id)
        if document.evolution_id and not can_view_confidential_evolution(self.request.user, document.evolution):
            self.permission_denied(
                self.request,
                message="Você não pode acessar documentos desta evolução confidencial.",
            )
        return document


class SecureClinicalDocumentListCreateView(SecureClinicalDocumentMixin, APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, patient_id):
        patient = self.get_patient(patient_id)
        queryset = ClinicalDocument.objects.filter(
            patient=patient,
            deleted_at__isnull=True,
        ).select_related("evolution", "evolution__created_by", "uploaded_by")
        if not has_explicit_records_permission(request.user, "view_confidential_evolution"):
            queryset = queryset.filter(
                Q(evolution__isnull=True) | Q(evolution__is_confidential=False) | Q(evolution__created_by=request.user)
            )
        category = request.query_params.get("category")
        if category:
            queryset = queryset.filter(category=category)
        return Response(
            SecureClinicalDocumentSerializer(
                queryset,
                many=True,
                context={"request": request, "patient": patient},
            ).data
        )

    def post(self, request, patient_id):
        patient = self.get_patient(patient_id)
        serializer = SecureClinicalDocumentSerializer(
            data=request.data,
            context={"request": request, "patient": patient},
        )
        serializer.is_valid(raise_exception=True)
        evolution = serializer.validated_data.get("evolution")
        if evolution and not can_view_confidential_evolution(request.user, evolution):
            self.permission_denied(
                request,
                message="Você não pode anexar arquivos a esta evolução confidencial.",
            )
        uploaded_file = serializer.validated_data.get("file")
        if not uploaded_file:
            return Response(
                {"file": ["Selecione um arquivo."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        original_name = sanitize_original_filename(uploaded_file.name)
        checksum = ClinicalDocument.calculate_checksum(uploaded_file)
        document = create_quarantined_document(
            patient=patient,
            uploaded_by=request.user,
            uploaded_file=uploaded_file,
            original_name=original_name,
            content_type=uploaded_file.content_type,
            checksum=checksum,
            validated_data=serializer.validated_data,
        )
        log_access(
            request,
            AuditLog.Action.CREATE,
            obj=document,
            obj_repr=f"Documento clínico #{document.id}:quarentena",
        )
        return Response(
            SecureClinicalDocumentSerializer(
                document,
                context={"request": request, "patient": patient},
            ).data,
            status=status.HTTP_202_ACCEPTED,
        )


class SecureClinicalDocumentDetailView(SecureClinicalDocumentMixin, APIView):
    def patch(self, request, pk):
        document = self.get_document(pk)
        if "file" in request.data:
            return Response(
                {"file": ["Envie uma nova versão pelo fluxo de upload seguro."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = SecureClinicalDocumentSerializer(
            document,
            data=request.data,
            partial=True,
            context={"request": request, "patient": document.patient},
        )
        serializer.is_valid(raise_exception=True)
        evolution = serializer.validated_data.get("evolution")
        if evolution and not can_view_confidential_evolution(request.user, evolution):
            self.permission_denied(
                request,
                message="Você não pode vincular o documento a esta evolução confidencial.",
            )
        serializer.save()
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=document,
            obj_repr=f"Documento clínico #{document.id}",
        )
        return Response(serializer.data)

    def delete(self, request, pk):
        document = self.get_document(pk)
        document.soft_delete()
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=document,
            obj_repr=f"Documento arquivado #{document.id}",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class SecureClinicalDocumentDownloadView(SecureClinicalDocumentMixin, APIView):
    def get(self, request, pk):
        document = self.get_document(pk)
        if not document.is_downloadable:
            return Response(
                {
                    "error": {
                        "code": "CLINICAL_DOCUMENT_NOT_RELEASED",
                        "message": "O arquivo ainda não está disponível para download.",
                    },
                    "scan_status": document.scan_status,
                },
                status=status.HTTP_423_LOCKED,
            )
        try:
            stream = document.file.open("rb")
        except FileNotFoundError as exc:
            raise Http404("Arquivo não encontrado no armazenamento.") from exc
        log_access(
            request,
            AuditLog.Action.EXPORT,
            obj=document,
            obj_repr=f"Download do documento #{document.id}",
        )
        response = FileResponse(
            stream,
            as_attachment=True,
            filename=document.original_name,
            content_type=document.content_type,
        )
        response["Cache-Control"] = "private, no-store, max-age=0"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        response["X-Content-Type-Options"] = "nosniff"
        response["Cross-Origin-Resource-Policy"] = "same-origin"
        return response
