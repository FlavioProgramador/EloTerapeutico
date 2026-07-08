# mypy: ignore-errors
"""Serializers do módulo de documentos."""

from __future__ import annotations

import json

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.patients.models import Patient

from apps.documents.models import DocumentTemplate, GeneratedDocument
from apps.documents.services.placeholders import (
    build_document_context,
    render_safe_markdown,
    sample_document_context,
    validate_template_content,
)
from apps.documents.services.core_services import DocumentDomainError, create_generated_document


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
        request = self.context.get("request")
        if request and request.user.is_secretary:
            raise serializers.ValidationError("Secretárias não possuem acesso a templates clínicos.")
        if request:
            name = attrs.get("name", getattr(self.instance, "name", ""))
            duplicate = DocumentTemplate.objects.filter(
                owner=request.user,
                name=name,
                archived_at__isnull=True,
            )
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

    def build_context(self, template: DocumentTemplate) -> dict[str, str]:
        request = self.context["request"]
        patient_id = self.validated_data.get("patient_id")
        if not patient_id:
            return sample_document_context()
        patient = Patient.objects.filter(
            pk=patient_id,
            therapist=request.user,
            deleted_at__isnull=True,
        ).first()
        if not patient:
            raise serializers.ValidationError({"patient_id": "Paciente não autorizado."})
        return build_document_context(
            patient=patient,
            professional=request.user,
            document_number="PRÉVIA",
            local_emissao=self.validated_data.get("local_emissao", ""),
        )

    def render(self, template: DocumentTemplate) -> dict[str, str]:
        context = self.build_context(template)
        return {
            "title": template.name,
            "header_html": render_safe_markdown(template.header_content, context) if template.header_content else "",
            "content_html": render_safe_markdown(template.content, context),
            "footer_html": render_safe_markdown(template.footer_content, context) if template.footer_content else "",
        }


class GeneratedDocumentCreateSerializer(serializers.Serializer):
    template_public_id = serializers.UUIDField()
    patient_id = serializers.IntegerField(min_value=1)
    title = serializers.CharField(required=False, allow_blank=True, max_length=200)
    local_emissao = serializers.CharField(required=False, allow_blank=True, max_length=160)

    def validate(self, attrs):
        request = self.context["request"]
        template = DocumentTemplate.objects.filter(
            public_id=attrs["template_public_id"],
            owner=request.user,
            is_library_template=False,
            archived_at__isnull=True,
        ).first()
        if not template:
            raise serializers.ValidationError({"template_public_id": "Template não autorizado."})
        patient = Patient.objects.filter(
            pk=attrs["patient_id"],
            therapist=request.user,
            deleted_at__isnull=True,
        ).first()
        if not patient:
            raise serializers.ValidationError({"patient_id": "Paciente não autorizado."})
        attrs["template"] = template
        attrs["patient"] = patient
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        try:
            result = create_generated_document(
                actor=request.user,
                patient=validated_data["patient"],
                template=validated_data["template"],
                title=validated_data.get("title", ""),
                local_emissao=validated_data.get("local_emissao", ""),
                idempotency_key=request.headers.get("Idempotency-Key"),
            )
        except DocumentDomainError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        self.context["created"] = result.created
        return result.document


class GeneratedDocumentListSerializer(serializers.ModelSerializer):
    public_id = serializers.UUIDField(read_only=True)
    patient_name = serializers.CharField(source="patient.display_name", read_only=True)
    professional_name = serializers.CharField(source="professional.full_name", read_only=True)
    document_type_display = serializers.CharField(source="get_document_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedDocument
        fields = (
            "public_id",
            "document_number",
            "title",
            "patient",
            "patient_name",
            "professional_name",
            "document_type",
            "document_type_display",
            "category",
            "status",
            "status_display",
            "generated_at",
            "created_at",
            "updated_at",
            "download_url",
        )
        read_only_fields = fields

    def get_download_url(self, obj):
        if obj.status != GeneratedDocument.Status.COMPLETED or not obj.pdf_file:
            return None
        return f"/api/v1/documents/generated/{obj.public_id}/download/"


class GeneratedDocumentDetailSerializer(GeneratedDocumentListSerializer):
    template_public_id = serializers.UUIDField(source="template.public_id", read_only=True, allow_null=True)
    template_name = serializers.CharField(source="template_name_snapshot", read_only=True)
    content = serializers.CharField(source="rendered_content", read_only=True)

    class Meta(GeneratedDocumentListSerializer.Meta):
        fields = GeneratedDocumentListSerializer.Meta.fields + (
            "template_public_id",
            "template_name",
            "template_version_snapshot",
            "content",
            "include_professional_identification_snapshot",
            "include_clinic_identification_snapshot",
            "requires_signature_snapshot",
            "pdf_hash",
            "signature_hash",
            "professional_registration_snapshot",
            "signed_at",
            "failure_reason",
            "archived_at",
        )
        read_only_fields = fields


class GeneratedDocumentDraftUpdateSerializer(serializers.ModelSerializer):
    draft_content = serializers.CharField(source="template_content_snapshot", required=False)

    class Meta:
        model = GeneratedDocument
        fields = ("title", "draft_content")

    def validate(self, attrs):
        if self.instance.status != GeneratedDocument.Status.DRAFT:
            raise serializers.ValidationError("Somente documentos em rascunho podem ser editados.")
        return attrs

    def validate_draft_content(self, value: str) -> str:
        try:
            return validate_template_content(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages[0]) from exc

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        context = json.loads(instance.context_snapshot or "{}")
        instance.rendered_content = render_safe_markdown(
            instance.template_content_snapshot,
            context,
        )
        instance.save(update_fields=["rendered_content", "updated_at"])
        return instance
