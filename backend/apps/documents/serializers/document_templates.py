"""Serializers de templates de documentos."""

from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.documents.models import DocumentTemplate
from apps.documents.services.document_templates import DocumentPlaceholderService


class DocumentTemplateSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    document_type_display = serializers.CharField(source="get_document_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    author_name = serializers.CharField(source="created_by.full_name", read_only=True, allow_null=True)
    source_library_public_id = serializers.UUIDField(
        source="source_library_template.public_id", read_only=True, allow_null=True
    )

    class Meta:
        model = DocumentTemplate
        fields = (
            "public_id",
            "name",
            "description",
            "category",
            "document_type",
            "document_type_display",
            "specialty",
            "content",
            "header_content",
            "footer_content",
            "include_professional_identification",
            "include_clinic_identification",
            "requires_signature",
            "status",
            "status_display",
            "version",
            "usage_count",
            "author_name",
            "source_library_public_id",
            "is_library_template",
            "created_at",
            "updated_at",
            "archived_at",
        )
        read_only_fields = (
            "public_id",
            "version",
            "usage_count",
            "author_name",
            "source_library_public_id",
            "is_library_template",
            "created_at",
            "updated_at",
            "archived_at",
        )

    def validate_name(self, value: str) -> str:
        value = " ".join(value.split()).strip()
        if len(value) < 3:
            raise serializers.ValidationError("Informe um nome com pelo menos 3 caracteres.")
        return value

    def _validate_template_field(self, value: str, *, required: bool) -> str:
        value = (value or "").strip()
        if not value and not required:
            return ""
        try:
            return DocumentPlaceholderService.validate_content(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages[0]) from exc

    def validate_content(self, value: str) -> str:
        return self._validate_template_field(value, required=True)

    def validate_header_content(self, value: str) -> str:
        return self._validate_template_field(value, required=False)

    def validate_footer_content(self, value: str) -> str:
        return self._validate_template_field(value, required=False)

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.user.is_secretary:
            raise serializers.ValidationError("Secretárias não possuem acesso a templates clínicos.")
        if request:
            name = attrs.get("name", getattr(self.instance, "name", ""))
            duplicate = DocumentTemplate.objects.active_named_for(request.user, name)
            if self.instance:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise serializers.ValidationError({"name": "Já existe um template ativo com este nome."})
        return attrs


class DocumentTemplateListSerializer(DocumentTemplateSerializer):
    class Meta(DocumentTemplateSerializer.Meta):
        fields = tuple(
            field
            for field in DocumentTemplateSerializer.Meta.fields
            if field not in {"content", "header_content", "footer_content"}
        ) + ("content_preview",)

    content_preview = serializers.SerializerMethodField()

    def get_content_preview(self, obj) -> str:
        content = " ".join((obj.content or "").split())
        return content[:180] + ("…" if len(content) > 180 else "")


class TemplatePreviewRequestSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(required=False, min_value=1)
    local_emissao = serializers.CharField(required=False, allow_blank=True, max_length=160)
