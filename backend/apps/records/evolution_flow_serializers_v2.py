"""Ajustes de compatibilidade para escrita parcial de evoluções."""

from rest_framework import serializers

from .evolution_flow_serializers import EvolutionFlowSerializer as BaseSerializer
from .evolution_security import sanitize_clinical_markdown


class EvolutionFlowSerializer(BaseSerializer):
    """Preserva conteúdo existente em PATCH e fixa o formato de saída."""

    def validate(self, attrs):
        clinical_data = attrs.get("clinical_data", {})
        profile = getattr(self.instance, "clinical_data", None)
        supplied_content = attrs.get("content")
        supplied_observation = clinical_data.get("therapist_observations")
        existing_content = getattr(self.instance, "content", "") if self.instance else ""
        existing_observation = (
            getattr(profile, "therapist_observations", "") if profile else ""
        )
        source = (
            supplied_content
            if supplied_content is not None
            else supplied_observation
            if supplied_observation is not None
            else existing_content or existing_observation
        )
        normalized = sanitize_clinical_markdown(source)
        if not normalized:
            raise serializers.ValidationError(
                {"content": "Informe a evolução ou as anotações clínicas."}
            )

        if supplied_content is None and self.instance:
            attrs["content"] = existing_content
        if supplied_observation is None and self.instance:
            clinical_data["therapist_observations"] = existing_observation
        attrs["clinical_data"] = clinical_data
        return super().validate(attrs)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["content_format"] = "markdown"
        return data
