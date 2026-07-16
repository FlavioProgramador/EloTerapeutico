"""Serializers com validação reforçada para documentos clínicos."""

from rest_framework import serializers

from apps.records.api.serializers.clinical_serializers import ClinicalDocumentSerializer
from apps.records.services.document_upload_security import validate_clinical_document_upload
from apps.records.treatment_models import ClinicalDocument


class SecureClinicalDocumentSerializer(ClinicalDocumentSerializer):
    scan_status = serializers.CharField(read_only=True)
    scan_status_display = serializers.CharField(source="get_scan_status_display", read_only=True)
    scan_attempts = serializers.IntegerField(read_only=True)
    scanned_at = serializers.DateTimeField(read_only=True, allow_null=True)

    class Meta(ClinicalDocumentSerializer.Meta):
        fields = ClinicalDocumentSerializer.Meta.fields + (
            "scan_status",
            "scan_status_display",
            "scan_attempts",
            "scanned_at",
        )
        read_only_fields = ClinicalDocumentSerializer.Meta.read_only_fields + (
            "scan_status",
            "scan_status_display",
            "scan_attempts",
            "scanned_at",
        )

    def validate_file(self, uploaded_file):
        return validate_clinical_document_upload(uploaded_file)

    def get_status(self, obj):
        if obj.is_archived:
            return "archived"
        return {
            ClinicalDocument.ScanStatus.PENDING: "processing",
            ClinicalDocument.ScanStatus.SCANNING: "processing",
            ClinicalDocument.ScanStatus.CLEAN: "available",
            ClinicalDocument.ScanStatus.INFECTED: "rejected",
            ClinicalDocument.ScanStatus.FAILED: "failed",
        }.get(obj.scan_status, "processing")

    def get_status_display(self, obj):
        if obj.is_archived:
            return "Arquivado"
        return {
            ClinicalDocument.ScanStatus.PENDING: "Aguardando análise de segurança",
            ClinicalDocument.ScanStatus.SCANNING: "Analisando arquivo",
            ClinicalDocument.ScanStatus.CLEAN: "Disponível",
            ClinicalDocument.ScanStatus.INFECTED: "Arquivo rejeitado por segurança",
            ClinicalDocument.ScanStatus.FAILED: "Falha na análise de segurança",
        }.get(obj.scan_status, "Aguardando análise de segurança")

    def get_download_url(self, obj):
        if not obj.is_downloadable:
            return None
        return super().get_download_url(obj)
