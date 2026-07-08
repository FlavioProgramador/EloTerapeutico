"""Serializer de anexos de evoluções clínicas."""

from apps.records.api.serializers.evolution_flow_serializers import (
    EvolutionAttachmentSerializer as BaseEvolutionAttachmentSerializer,
)

from ..services.evolutions import create_evolution_attachment


class EvolutionAttachmentSerializer(BaseEvolutionAttachmentSerializer):
    def create(self, validated_data):
        uploaded_file = validated_data.pop("file")
        return create_evolution_attachment(
            evolution=self.context["evolution"],
            actor=self.context["request"].user,
            uploaded_file=uploaded_file,
        )
