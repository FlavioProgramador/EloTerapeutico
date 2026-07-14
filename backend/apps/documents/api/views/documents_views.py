"""Endpoints autenticados do módulo de documentos."""

from __future__ import annotations

from django.db.models import Q
from django.http import FileResponse
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.services.access_logging import AuditLog, log_access
from apps.documents.api.serializers.documents_serializers import (
    DocumentTemplateListSerializer,
    DocumentTemplateSerializer,
    GeneratedDocumentCreateSerializer,
    GeneratedDocumentDetailSerializer,
    GeneratedDocumentDraftUpdateSerializer,
    GeneratedDocumentListSerializer,
    TemplatePreviewRequestSerializer,
)
from apps.documents.models import DocumentTemplate, GeneratedDocument
from apps.documents.services.core_services import (
    duplicate_template,
    generate_pdf,
    import_library_template,
)
from apps.documents.services.placeholders import list_placeholders


class IsClinicalDocumentUser(IsAuthenticated):
    """Dados clínicos ficam indisponíveis para o papel de secretária."""

    def has_permission(self, request, view):
        return super().has_permission(request, view) and not request.user.is_secretary


class DocumentTemplateFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = DocumentTemplate
        fields = ("status", "category", "document_type", "specialty")

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(category__icontains=value)
            | Q(specialty__icontains=value)
        )


class GeneratedDocumentFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search")
    date_from = filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    date_to = filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = GeneratedDocument
        fields = ("patient", "professional", "document_type", "category", "status")

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value)
            | Q(document_number__icontains=value)
            | Q(patient__full_name__icontains=value)
            | Q(patient__social_name__icontains=value)
        )


class DocumentTemplateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsClinicalDocumentUser]
    lookup_field = "public_id"
    filterset_class = DocumentTemplateFilter
    ordering_fields = ("name", "created_at", "updated_at", "usage_count")
    ordering = ("name",)

    def get_queryset(self):
        return DocumentTemplate.objects.filter(
            owner=self.request.user,
            is_library_template=False,
        ).select_related("created_by", "source_library_template")

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
        if template.generated_documents.exists() or template.source_library_template_id:
            template.archive()
            log_access(
                request,
                AuditLog.Action.UPDATE,
                obj=template,
                obj_repr=f"Template de documento #{template.pk} arquivado",
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
        copy = duplicate_template(actor=request.user, template=template)
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
        template.archive()
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
        template.status = DocumentTemplate.Status.ACTIVE
        template.archived_at = None
        template.updated_by = request.user
        template.save(update_fields=["status", "archived_at", "updated_by", "updated_at"])
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
        template.status = DocumentTemplate.Status.INACTIVE
        template.updated_by = request.user
        template.save(update_fields=["status", "updated_by", "updated_at"])
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
        return DocumentTemplate.objects.filter(
            owner__isnull=True,
            is_library_template=True,
            status=DocumentTemplate.Status.ACTIVE,
            archived_at__isnull=True,
        ).select_related("created_by")

    @action(detail=True, methods=["post"], url_path="import")
    def import_template(self, request, public_id=None):
        library_template = self.get_object()
        template, created = import_library_template(
            actor=request.user,
            library_template=library_template,
        )
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


class GeneratedDocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsClinicalDocumentUser]
    lookup_field = "public_id"
    filterset_class = GeneratedDocumentFilter
    ordering_fields = ("created_at", "updated_at", "generated_at", "title")
    ordering = ("-created_at",)
    http_method_names = ("get", "post", "patch", "delete", "head", "options")

    def get_queryset(self):
        return GeneratedDocument.objects.filter(owner=self.request.user).select_related(
            "patient",
            "professional",
            "template",
        )

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
        if document.status == GeneratedDocument.Status.DRAFT and not document.pdf_file:
            log_access(
                request,
                AuditLog.Action.DELETE,
                obj=document,
                obj_repr=f"Rascunho de documento #{document.pk} excluído",
            )
            document.delete()
        else:
            document.archive()
            log_access(
                request,
                AuditLog.Action.UPDATE,
                obj=document,
                obj_repr=f"Documento #{document.pk} arquivado",
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def generate(self, request, public_id=None):
        document = self.get_object()
        document = generate_pdf(document=document, actor=request.user)
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
        document.archive()
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
        if document.status not in (
            GeneratedDocument.Status.DRAFT,
            GeneratedDocument.Status.FAILED,
        ):
            return Response(
                {"detail": "Somente rascunhos ou documentos com falha podem ser cancelados."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        document.status = GeneratedDocument.Status.CANCELLED
        document.save(update_fields=["status", "updated_at"])
        log_access(
            request,
            AuditLog.Action.UPDATE,
            obj=document,
            obj_repr=f"Documento #{document.pk} cancelado",
        )
        return Response(GeneratedDocumentDetailSerializer(document).data)


class PlaceholderListView(APIView):
    permission_classes = [IsClinicalDocumentUser]

    def get(self, request):
        return Response(list_placeholders())
