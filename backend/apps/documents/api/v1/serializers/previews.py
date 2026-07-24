# mypy: ignore-errors
"""Serializers de pré-visualização de templates."""

from rest_framework import serializers

from apps.documents.models import DocumentTemplate
from apps.documents.selectors import get_accessible_patient
from apps.documents.services.placeholders import (
    build_document_context,
    render_safe_markdown,
    sample_document_context,
)


class TemplatePreviewRequestSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(required=False, min_value=1)
    local_emissao = serializers.CharField(required=False, allow_blank=True, max_length=160)

    def build_context(self, template: DocumentTemplate) -> dict[str, str]:
        request = self.context["request"]
        patient_id = self.validated_data.get("patient_id")
        if not patient_id:
            return sample_document_context()
        from apps.organizations.services.tenant_context import ensure_request_organization
        organization, _ = ensure_request_organization(request=request, required=False)
        patient = get_accessible_patient(
            owner=request.user,
            patient_id=patient_id,
            organization=organization,
        )
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
