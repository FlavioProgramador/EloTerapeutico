"""Serializer de anexos de evoluções clínicas."""

from rest_framework import serializers

from apps.records.api.serializers.evolution_flow_serializers import (
    EvolutionAttachmentSerializer as BaseEvolutionAttachmentSerializer,
)

from ..services.evolutions import create_evolution_attachment


class EvolutionAttachmentSerializer(BaseEvolutionAttachmentSerializer):
    scan_status = serializers.CharField(read_only=True)
    scan_status_display = serializers.CharField(source="get_scan_status_display", read_only=True)

    class Meta(BaseEvolutionAttachmentSerializer.Meta):
        fields = BaseEvolutionAttachmentSerializer.Meta.fields + (
            "scan_status",
            "scan_status_display",
        )
        read_only_fields = BaseEvolutionAttachmentSerializer.Meta.read_only_fields + (
            "scan_status",
            "scan_status_display",
        )

    def get_download_url(self, obj):
        if not obj.is_downloadable:
            return None
        return super().get_download_url(obj)

    def get_preview_url(self, obj):
        if not obj.is_downloadable:
            return None
        return super().get_preview_url(obj)

    def create(self, validated_data):
        uploaded_file = validated_data.pop("file")
        return create_evolution_attachment(
            evolution=self.context["evolution"],
            actor=self.context["request"].user,
            uploaded_file=uploaded_file,
        )
