"""Views de documentos gerados."""

from django.http import FileResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.models import AuditLog
from apps.audit.services import log_access
from apps.documents.exceptions import DocumentDomainError
from apps.documents.filters import GeneratedDocumentFilter
from apps.documents.selectors import generated_documents_for_owner
from apps.documents.services import (
    archive_document,
    cancel_document,
    generate_pdf,
    prepare_document_download,
    remove_or_archive_document,
)

from ..permissions import IsClinicalDocumentUser
from ..serializers import (
    GeneratedDocumentCreateSerializer,
    GeneratedDocumentDetailSerializer,
    GeneratedDocumentDraftUpdateSerializer,
    GeneratedDocumentListSerializer,
)


class GeneratedDocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsClinicalDocumentUser]
    lookup_field = "public_id"
    filterset_class = GeneratedDocumentFilter
    ordering_fields = ("created_at", "updated_at", "generated_at", "title")
    ordering = ("-created_at",)
    http_method_names = ("get", "post", "patch", "delete", "head", "options")

    def get_queryset(self):
        return generated_documents_for_owner(owner=self.request.user)

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
        return Response(
            GeneratedDocumentDetailSerializer(
                document,
                context=self.get_serializer_context(),
            ).data
        )

    def destroy(self, request, *args, **kwargs):
        result = remove_or_archive_document(
            actor=request.user,
            document=self.get_object(),
        )
        if result.archived and result.document is not None:
            log_access(
                request,
                AuditLog.Action.UPDATE,
                obj=result.document,
                obj_repr=f"Documento #{result.object_id} arquivado",
            )
        else:
            log_access(
                request,
                AuditLog.Action.DELETE,
                obj_repr=f"Rascunho de documento #{result.object_id} excluído",
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def generate(self, request, public_id=None):
        document = self.get_object()
        try:
            document = generate_pdf(document=document, actor=request.user)
        except DocumentDomainError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        log_access(
            request,
            AuditLog.Action.EXPORT,
            obj=document,
            obj_repr=f"PDF do documento #{document.pk} gerado",
        )
        return Response(
            GeneratedDocumentDetailSerializer(
                document,
                context=self.get_serializer_context(),
            ).data
        )

    @action(detail=True, methods=["get"])
    def download(self, request, public_id=None):
        document = self.get_object()
        try:
            download = prepare_document_download(
                actor=request.user,
                document=document,
            )
        except DocumentDomainError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        log_access(
            request,
            AuditLog.Action.EXPORT,
            obj=document,
            obj_repr=f"PDF do documento #{document.pk} baixado",
        )
        response = FileResponse(
            download.file,
            as_attachment=True,
            filename=download.filename,
            content_type=download.content_type,
        )
        response["Cache-Control"] = "private, no-store, max-age=0"
        response["X-Content-Type-Options"] = "nosniff"
        return response

    @action(detail=True, methods=["post"])
    def archive(self, request, public_id=None):
        document = archive_document(
            actor=request.user,
            document=self.get_object(),
        )
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=document,
            obj_repr=f"Documento #{document.pk} arquivado",
        )
        return Response(
            GeneratedDocumentDetailSerializer(
                document,
                context=self.get_serializer_context(),
            ).data
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, public_id=None):
        try:
            document = cancel_document(
                actor=request.user,
                document=self.get_object(),
            )
        except DocumentDomainError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=document,
            obj_repr=f"Documento #{document.pk} cancelado",
        )
        return Response(
            GeneratedDocumentDetailSerializer(
                document,
                context=self.get_serializer_context(),
            ).data
        )
