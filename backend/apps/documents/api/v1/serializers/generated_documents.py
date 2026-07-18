# mypy: ignore-errors
"""Serializers de documentos gerados."""

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.documents.exceptions import DocumentDomainError
from apps.documents.models import GeneratedDocument
from apps.documents.selectors import get_accessible_patient, get_owned_template
from apps.documents.services import create_generated_document, update_document_draft
from apps.documents.services.placeholders import validate_template_content


class GeneratedDocumentCreateSerializer(serializers.Serializer):
    template_public_id = serializers.UUIDField()
    patient_id = serializers.IntegerField(min_value=1)
    title = serializers.CharField(required=False, allow_blank=True, max_length=200)
    local_emissao = serializers.CharField(required=False, allow_blank=True, max_length=160)

    def validate(self, attrs):
        request = self.context["request"]
        template = get_owned_template(owner=request.user, public_id=attrs["template_public_id"])
        if not template:
            raise serializers.ValidationError({"template_public_id": "Template não autorizado."})
        patient = get_accessible_patient(owner=request.user, patient_id=attrs["patient_id"])
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
        try:
            return update_document_draft(
                actor=self.context["request"].user,
                document=instance,
                validated_data=validated_data,
            )
        except DocumentDomainError as exc:
            raise serializers.ValidationError(str(exc)) from exc
