# mypy: ignore-errors
"""Serializers de templates de documentos."""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.documents.models import DocumentTemplate
from apps.documents.selectors import template_name_exists
from apps.documents.services import create_template, update_template
from apps.documents.services.placeholders import validate_template_content


class DocumentTemplateSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    document_type_display = serializers.CharField(
        source="get_document_type_display",
        read_only=True,
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    author_name = serializers.CharField(
        source="created_by.full_name",
        read_only=True,
        allow_null=True,
    )
    source_library_public_id = serializers.UUIDField(
        source="source_library_template.public_id",
        read_only=True,
        allow_null=True,
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

    def _organization(self):
        request = self.context.get("request")
        organization = getattr(request, "organization", None)
        if organization is None:
            raise serializers.ValidationError(
                {"organization": "Selecione uma organização."}
            )
        return organization

    def validate_name(self, value: str) -> str:
        value = " ".join(value.split()).strip()
        if len(value) < 3:
            raise serializers.ValidationError(
                "Informe um nome com pelo menos 3 caracteres."
            )
        return value

    def _validate_template_field(self, value: str, *, required: bool) -> str:
        value = (value or "").strip()
        if not value and not required:
            return ""
        try:
            return validate_template_content(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages[0]) from exc

    def validate_content(self, value: str) -> str:
        return self._validate_template_field(value, required=True)

    def validate_header_content(self, value: str) -> str:
        return self._validate_template_field(value, required=False)

    def validate_footer_content(self, value: str) -> str:
        return self._validate_template_field(value, required=False)

    def validate(self, attrs):
        organization = self._organization()
        name = attrs.get("name", getattr(self.instance, "name", ""))
        if template_name_exists(
            organization=organization,
            name=name,
            exclude_id=self.instance.pk if self.instance else None,
        ):
            raise serializers.ValidationError(
                {"name": "Já existe um template ativo com este nome."}
            )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return create_template(
            actor=request.user,
            organization=self._organization(),
            validated_data=validated_data,
        )

    def update(self, instance, validated_data):
        request = self.context["request"]
        return update_template(
            actor=request.user,
            organization=self._organization(),
            template=instance,
            validated_data=validated_data,
        )


class DocumentTemplateListSerializer(DocumentTemplateSerializer):
    content_preview = serializers.SerializerMethodField()

    class Meta(DocumentTemplateSerializer.Meta):
        fields = tuple(
            field
            for field in DocumentTemplateSerializer.Meta.fields
            if field not in {"content", "header_content", "footer_content"}
        ) + ("content_preview",)

    def get_content_preview(self, obj) -> str:
        content = " ".join((obj.content or "").split())
        return content[:180] + ("…" if len(content) > 180 else "")
