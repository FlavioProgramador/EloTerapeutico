"""Serializers de documentos gerados."""

from __future__ import annotations

import json

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.documents.models import DocumentTemplate, GeneratedDocument
from apps.documents.services.document_templates import DocumentDomainError, DocumentPlaceholderService
from apps.documents.services.generated_documents import GeneratedDocumentService
from apps.patients.models import Patient


class GeneratedDocumentCreateSerializer(serializers.Serializer):
    template_public_id = serializers.UUIDField()
    patient_id = serializers.IntegerField(min_value=1)
    title = serializers.CharField(required=False, allow_blank=True, max_length=200)
    local_emissao = serializers.CharField(required=False, allow_blank=True, max_length=160)

    def validate(self, attrs):
        request = self.context["request"]
        template = (
            DocumentTemplate.objects.private_for(request.user)
            .filter(
                public_id=attrs["template_public_id"],
                archived_at__isnull=True,
            )
            .first()
        )
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
            result = GeneratedDocumentService.create(
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
            return DocumentPlaceholderService.validate_content(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages[0]) from exc

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        context = json.loads(instance.context_snapshot or "{}")
        instance.rendered_content = DocumentPlaceholderService.render(
            instance.template_content_snapshot,
            context,
        )
        instance.save(update_fields=["rendered_content", "updated_at"])
        return instance
