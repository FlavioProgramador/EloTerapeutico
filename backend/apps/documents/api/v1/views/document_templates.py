"""Views de templates e biblioteca documental."""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.audit.models import AuditLog
from apps.audit.services import log_access
from apps.documents.exceptions import DocumentDomainError
from apps.documents.filters import DocumentTemplateFilter
from apps.documents.selectors import library_templates, owned_templates
from apps.documents.services import (
    activate_template,
    archive_template,
    deactivate_template,
    duplicate_template,
    import_library_template,
    remove_or_archive_template,
)

from ..permissions import IsClinicalDocumentUser
from ..serializers import (
    DocumentTemplateListSerializer,
    DocumentTemplateSerializer,
    TemplatePreviewRequestSerializer,
)


class DocumentTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsClinicalDocumentUser]
    lookup_field = "public_id"
    filterset_class = DocumentTemplateFilter
    ordering_fields = ("name", "created_at", "updated_at", "usage_count")
    ordering = ("name",)

    def get_queryset(self):
        return owned_templates(owner=self.request.user)

    def get_serializer_class(self):
        if self.action == "list":
            return DocumentTemplateListSerializer
        return DocumentTemplateSerializer

    def perform_create(self, serializer):
        template = serializer.save()
        log_access(
            self.request,
            AuditLog.Action.CREATE,
            obj=template,
            obj_repr=f"Template de documento #{template.pk} criado",
        )

    def perform_update(self, serializer):
        template = serializer.save()
        log_access(
            self.request,
            AuditLog.Action.UPDATE,
            obj=template,
            obj_repr=f"Template de documento #{template.pk} atualizado",
        )

    def destroy(self, request, *args, **kwargs):
        result = remove_or_archive_template(
            actor=request.user,
            template=self.get_object(),
        )
        if result.archived and result.template is not None:
            log_access(
                request,
                AuditLog.Action.UPDATE,
                obj=result.template,
                obj_repr=f"Template de documento #{result.object_id} arquivado",
            )
        else:
            log_access(
                request,
                AuditLog.Action.DELETE,
                obj_repr=f"Template de documento #{result.object_id} excluído",
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def duplicate(self, request, public_id=None):
        template = self.get_object()
        try:
            copy = duplicate_template(actor=request.user, template=template)
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
        template = archive_template(
            actor=request.user,
            template=self.get_object(),
        )
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=template,
            obj_repr=f"Template de documento #{template.pk} arquivado",
        )
        return Response(DocumentTemplateSerializer(template).data)

    @action(detail=True, methods=["post"])
    def activate(self, request, public_id=None):
        template = activate_template(actor=request.user, template=self.get_object())
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=template,
            obj_repr=f"Template de documento #{template.pk} ativado",
        )
        return Response(DocumentTemplateSerializer(template).data)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, public_id=None):
        template = deactivate_template(actor=request.user, template=self.get_object())
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
        return library_templates()

    @action(detail=True, methods=["post"], url_path="import")
    def import_template(self, request, public_id=None):
        library_template = self.get_object()
        try:
            template, created = import_library_template(
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
