"""Serializer canônico do fluxo de evoluções clínicas."""

from ..evolution_flow_serializers import (
    ClinicalEvolutionTemplateSerializer,
    EvolutionAppointmentOptionSerializer,
    EvolutionFlowSerializer as BaseEvolutionFlowSerializer,
)
from ..services.evolutions import create_evolution, update_evolution
from .evolution_serializer_fields import EvolutionFlowReadFieldsMixin
from .evolution_serializer_support import preserve_partial_evolution_content


class EvolutionFlowSerializer(
    EvolutionFlowReadFieldsMixin,
    BaseEvolutionFlowSerializer,
):
    class Meta(BaseEvolutionFlowSerializer.Meta):
        fields = BaseEvolutionFlowSerializer.Meta.fields + (
            "addenda_count",
            "attached_documents_count",
            "linked_goal_ids",
        )
        read_only_fields = BaseEvolutionFlowSerializer.Meta.read_only_fields + (
            "addenda_count",
            "attached_documents_count",
            "linked_goal_ids",
        )

    def validate(self, attrs):
        attrs = preserve_partial_evolution_content(
            instance=self.instance,
            attrs=attrs,
        )
        return super().validate(attrs)

    def create(self, validated_data):
        return create_evolution(
            patient=self.context["patient"],
            actor=self.context["request"].user,
            validated_data=validated_data,
        )

    def update(self, instance, validated_data):
        return update_evolution(
            evolution=instance,
            actor=self.context["request"].user,
            validated_data=validated_data,
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["content_format"] = "markdown"
        return data


__all__ = [
    "ClinicalEvolutionTemplateSerializer",
    "EvolutionAppointmentOptionSerializer",
    "EvolutionFlowSerializer",
]
