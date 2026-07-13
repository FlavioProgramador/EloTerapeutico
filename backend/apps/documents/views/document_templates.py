"""Views de templates de documentos."""

from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.filters.document_templates import DocumentTemplateFilter
from apps.documents.models import DocumentTemplate
from apps.documents.serializers.document_templates import (
    DocumentTemplateListSerializer,
    DocumentTemplateSerializer,
    TemplatePreviewRequestSerializer,
)
from apps.documents.services.document_templates import (
    DocumentDomainError,
    DocumentPlaceholderService,
    DocumentTemplateService,
)
from apps.documents.views import IsClinicalDocumentUser
from core.audit import AuditLog, log_access


class DocumentTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsClinicalDocumentUser]
    lookup_field = "public_id"
    filterset_class = DocumentTemplateFilter
    ordering_fields = ("name", "created_at", "updated_at", "usage_count")
    ordering = ("name",)

    def get_queryset(self):
        return DocumentTemplate.objects.private_for(self.request.user).for_template_api()

    def get_serializer_class(self):
        if self.action == "list":
            return DocumentTemplateListSerializer
        return DocumentTemplateSerializer

    def perform_create(self, serializer):
        template = serializer.save(
            owner=self.request.user,
            created_by=self.request.user,
            updated_by=self.request.user,
            is_library_template=False,
        )
        log_access(
            self.request,
            AuditLog.Action.CREATE,
            obj=template,
            obj_repr=f"Template de documento #{template.pk} criado",
        )

    def perform_update(self, serializer):
        template = serializer.save(
            updated_by=self.request.user,
            version=serializer.instance.version + 1,
        )
        log_access(
            self.request,
            AuditLog.Action.UPDATE,
            obj=template,
            obj_repr=f"Template de documento #{template.pk} atualizado",
        )

    def destroy(self, request, *args, **kwargs):
        template = self.get_object()
        try:
            action, affected_template = DocumentTemplateService.resolve_removal(actor=request.user, template=template)
        except DocumentDomainError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if action == "archived":
            log_access(
                request,
                AuditLog.Action.UPDATE,
                obj=affected_template,
                obj_repr=f"Template de documento #{affected_template.pk} arquivado",
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        log_access(
            request,
            AuditLog.Action.DELETE,
            obj=template,
            obj_repr=f"Template de documento #{template.pk} excluído",
        )
        template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, public_id=None):
        template = self.get_object()
        try:
            copy = DocumentTemplateService.duplicate(actor=request.user, template=template)
        except DocumentDomainError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        log_access(
            request,
            AuditLog.Action.CREATE,
            obj=copy,
            obj_repr=f"Template de documento #{template.pk} duplicado como #{copy.pk}",
        )
        return Response(DocumentTemplateSerializer(copy).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def archive(self, request, public_id=None):
        template = self.get_object()
        try:
            template = DocumentTemplateService.archive(actor=request.user, template=template)
        except DocumentDomainError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=template,
            obj_repr=f"Template de documento #{template.pk} arquivado",
        )
        return Response(DocumentTemplateSerializer(template).data)

    @action(detail=True, methods=["post"])
    def activate(self, request, public_id=None):
        template = self.get_object()
        try:
            template = DocumentTemplateService.activate(actor=request.user, template=template)
        except DocumentDomainError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=template,
            obj_repr=f"Template de documento #{template.pk} ativado",
        )
        return Response(DocumentTemplateSerializer(template).data)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, public_id=None):
        template = self.get_object()
        try:
            template = DocumentTemplateService.deactivate(actor=request.user, template=template)
        except DocumentDomainError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=template,
            obj_repr=f"Template de documento #{template.pk} inativado",
        )
        return Response(DocumentTemplateSerializer(template).data)

    @action(detail=True, methods=["post"])
    def preview(self, request, public_id=None):
        template = self.get_object()
        serializer = TemplatePreviewRequestSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        log_access(
            request,
            AuditLog.Action.VIEW,
            obj=template,
            obj_repr=f"Prévia do template de documento #{template.pk}",
        )
        return Response(serializer.render(template))


class DocumentLibraryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsClinicalDocumentUser]
    lookup_field = "public_id"
    serializer_class = DocumentTemplateSerializer
    filterset_class = DocumentTemplateFilter
    ordering_fields = ("name", "specialty", "category", "document_type")
    ordering = ("name",)

    def get_serializer_class(self):
        if self.action == "list":
            return DocumentTemplateListSerializer
        return DocumentTemplateSerializer

    def get_queryset(self):
        return DocumentTemplate.objects.active_library().for_library_api()

    @action(detail=True, methods=["post"], url_path="import")
    def import_template(self, request, public_id=None):
        library_template = self.get_object()
        try:
            template, created = DocumentTemplateService.import_from_library(
                actor=request.user,
                library_template=library_template,
            )
        except DocumentDomainError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if created:
            log_access(
                request,
                AuditLog.Action.CREATE,
                obj=template,
                obj_repr=f"Template da biblioteca #{library_template.pk} importado",
            )
        return Response(
            DocumentTemplateSerializer(template).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def preview(self, request, public_id=None):
        template = self.get_object()
        serializer = TemplatePreviewRequestSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.render(template))


class PlaceholderListView(APIView):
    permission_classes = [IsClinicalDocumentUser]

    def get(self, request):
        return Response(DocumentPlaceholderService.list_all())
