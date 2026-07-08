# mypy: ignore-errors
"""Serializer canônico do fluxo de evoluções clínicas."""

from rest_framework import serializers

from apps.records.api.serializers.evolution_flow_serializers import (
    EvolutionAppointmentOptionSerializer,
)
from apps.records.api.serializers.evolution_flow_serializers import (
    EvolutionFlowSerializer as BaseEvolutionFlowSerializer,
)
from apps.records.models.templates import ClinicalEvolutionTemplate
from apps.records.services.evolution_security import sanitize_clinical_markdown

from ..services.evolutions import create_evolution, update_evolution
from .evolution_serializer_fields import EvolutionFlowReadFieldsMixin
from .evolution_serializer_support import preserve_partial_evolution_content


class ClinicalEvolutionTemplateSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    is_system = serializers.SerializerMethodField()
    content_preview = serializers.SerializerMethodField()

    class Meta:
        model = ClinicalEvolutionTemplate
        fields = (
            "id",
            "name",
            "description",
            "category",
            "specialty",
            "content",
            "content_preview",
            "owner",
            "owner_name",
            "is_system",
            "is_active",
            "sort_order",
            "usage_count",
            "archived_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "owner",
            "owner_name",
            "is_system",
            "usage_count",
            "archived_at",
            "created_at",
            "updated_at",
        )

    def get_is_system(self, obj):
        return obj.owner_id is None

    def get_content_preview(self, obj):
        content = " ".join((obj.content or "").split())
        return content[:180] + ("…" if len(content) > 180 else "")

    def validate_name(self, value):
        value = " ".join(value.split()).strip()
        if len(value) < 2:
            raise serializers.ValidationError("Informe um nome para o template.")
        return value

    def validate_content(self, value):
        value = sanitize_clinical_markdown(value)
        if not value:
            raise serializers.ValidationError("O template não pode estar vazio.")
        if len(value) > 50_000:
            raise serializers.ValidationError("O template deve possuir no máximo 50.000 caracteres.")
        return value


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
