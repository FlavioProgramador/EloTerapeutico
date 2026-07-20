"""Detalhe, remoção e download de anexos de evoluções."""

from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.audit.services import log_access
from apps.records.api.views.clinical_views import ClinicalPatientMixin
from apps.records.services.evolution_security import can_view_confidential_evolution

from ..models import ClinicalDocument
from ..services.evolutions import remove_evolution_attachment


class EvolutionAttachmentDetailView(ClinicalPatientMixin, APIView):
    def get_document(self, evolution_id, attachment_id):
        evolution = self.get_evolution(evolution_id)
        document = get_object_or_404(
            ClinicalDocument,
            pk=attachment_id,
            evolution=evolution,
            deleted_at__isnull=True,
        )
        return evolution, document

    def delete(self, request, evolution_id, attachment_id):
        evolution, document = self.get_document(evolution_id, attachment_id)
        remove_evolution_attachment(
            evolution=evolution,
            document=document,
            actor=request.user,
        )
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=document,
            obj_repr=f"Anexo #{document.id} removido da evolução #{evolution.id}",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class EvolutionAttachmentDownloadView(EvolutionAttachmentDetailView):
    def get(self, request, evolution_id, attachment_id):
        evolution, document = self.get_document(evolution_id, attachment_id)
        if not can_view_confidential_evolution(request.user, evolution):
            self.permission_denied(
                request,
                message="Você não pode acessar este anexo.",
            )
        if not document.is_downloadable:
            return Response(
                {
                    "error": {
                        "code": "CLINICAL_ATTACHMENT_NOT_RELEASED",
                        "message": "O anexo ainda não está disponível para download.",
                    },
                    "scan_status": document.scan_status,
                },
                status=status.HTTP_423_LOCKED,
            )
        try:
            stream = document.file.open("rb")
        except FileNotFoundError as exc:
            raise Http404("Arquivo não encontrado no armazenamento.") from exc
        inline = request.query_params.get("inline") == "1" and document.content_type.startswith("image/")
        log_access(
            request,
            AuditLog.Action.EXPORT,
            obj=document,
            obj_repr=f"Acesso ao anexo #{document.id} da evolução #{evolution.id}",
        )
        response = FileResponse(
            stream,
            as_attachment=not inline,
            filename=document.original_name,
            content_type=document.content_type,
        )
        response["Cache-Control"] = "private, no-store, max-age=0"
        response["X-Content-Type-Options"] = "nosniff"
        response["Cross-Origin-Resource-Policy"] = "same-origin"
        return response
