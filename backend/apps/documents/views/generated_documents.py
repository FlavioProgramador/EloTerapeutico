"""Views de documentos gerados."""

from __future__ import annotations

from django.http import FileResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.documents.filters.generated_documents import GeneratedDocumentFilter
from apps.documents.models import GeneratedDocument
from apps.documents.serializers.generated_documents import (
    GeneratedDocumentCreateSerializer,
    GeneratedDocumentDetailSerializer,
    GeneratedDocumentDraftUpdateSerializer,
    GeneratedDocumentListSerializer,
)
from apps.documents.services.document_templates import DocumentDomainError
from apps.documents.services.generated_documents import GeneratedDocumentService
from apps.documents.views import IsClinicalDocumentUser
from core.audit import AuditLog, log_access


class GeneratedDocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsClinicalDocumentUser]
    lookup_field = "public_id"
    filterset_class = GeneratedDocumentFilter
    ordering_fields = ("created_at", "updated_at", "generated_at", "title")
    ordering = ("-created_at",)
    http_method_names = ("get", "post", "patch", "delete", "head", "options")

    def get_queryset(self):
        return GeneratedDocument.objects.for_owner(self.request.user).with_document_relations()

    def get_serializer_class(self):
        if self.action == "create":
            return GeneratedDocumentCreateSerializer
        if self.action == "list":
            return GeneratedDocumentListSerializer
        if self.action in ("partial_update", "update"):
            return GeneratedDocumentDraftUpdateSerializer
        return GeneratedDocumentDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        was_created = serializer.context.get("created", True)
        if was_created:
            log_access(
                request,
                AuditLog.Action.CREATE,
                obj=document,
                obj_repr=f"Documento gerado #{document.pk} criado como rascunho",
            )
        response_serializer = GeneratedDocumentDetailSerializer(
            document,
            context=self.get_serializer_context(),
        )
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED if was_created else status.HTTP_200_OK,
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=document,
            obj_repr=f"Rascunho de documento #{document.pk} atualizado",
        )
        return Response(GeneratedDocumentDetailSerializer(document).data)

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        try:
            action, affected_document = GeneratedDocumentService.resolve_removal(actor=request.user, document=document)
        except DocumentDomainError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if action == "deleted":
            log_access(
                request,
                AuditLog.Action.DELETE,
                obj=document,
                obj_repr=f"Rascunho de documento #{document.pk} excluído",
            )
            document.delete()
        else:
            log_access(
                request,
                AuditLog.Action.UPDATE,
                obj=affected_document,
                obj_repr=f"Documento #{affected_document.pk} arquivado",
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def generate(self, request, public_id=None):
        document = self.get_object()
        try:
            document = GeneratedDocumentService.generate_pdf(document=document, actor=request.user)
        except DocumentDomainError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        log_access(
            request,
            AuditLog.Action.EXPORT,
            obj=document,
            obj_repr=f"PDF do documento #{document.pk} gerado",
        )
        return Response(GeneratedDocumentDetailSerializer(document).data)

    @action(detail=True, methods=["get"])
    def download(self, request, public_id=None):
        document = self.get_object()
        if document.status != GeneratedDocument.Status.COMPLETED or not document.pdf_file:
            return Response(
                {"detail": "O arquivo ainda não está disponível."},
                status=status.HTTP_409_CONFLICT,
            )
        log_access(
            request,
            AuditLog.Action.EXPORT,
            obj=document,
            obj_repr=f"PDF do documento #{document.pk} baixado",
        )
        document.pdf_file.open("rb")
        response = FileResponse(
            document.pdf_file,
            as_attachment=True,
            filename=f"{document.document_number}.pdf",
            content_type="application/pdf",
        )
        response["Cache-Control"] = "private, no-store, max-age=0"
        response["X-Content-Type-Options"] = "nosniff"
        return response

    @action(detail=True, methods=["post"])
    def archive(self, request, public_id=None):
        document = self.get_object()
        try:
            document = GeneratedDocumentService.archive(actor=request.user, document=document)
        except DocumentDomainError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=document,
            obj_repr=f"Documento #{document.pk} arquivado",
        )
        return Response(GeneratedDocumentDetailSerializer(document).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, public_id=None):
        document = self.get_object()
        try:
            document = GeneratedDocumentService.cancel(actor=request.user, document=document)
        except DocumentDomainError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=document,
            obj_repr=f"Documento #{document.pk} cancelado",
        )
        return Response(GeneratedDocumentDetailSerializer(document).data)
