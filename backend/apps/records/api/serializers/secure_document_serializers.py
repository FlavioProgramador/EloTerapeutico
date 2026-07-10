"""Serializers com validação reforçada para documentos clínicos."""

from apps.records.api.serializers.clinical_serializers import ClinicalDocumentSerializer
from apps.records.services.document_upload_security import validate_clinical_document_upload


class SecureClinicalDocumentSerializer(ClinicalDocumentSerializer):
    def validate_file(self, uploaded_file):
        return validate_clinical_document_upload(uploaded_file)
