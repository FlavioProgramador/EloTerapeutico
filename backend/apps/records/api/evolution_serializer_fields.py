"""Campos de leitura adicionais do fluxo de evoluções."""

from rest_framework import serializers


class EvolutionFlowReadFieldsMixin(metaclass=serializers.SerializerMetaclass):
    addenda_count = serializers.IntegerField(source="addenda.count", read_only=True)
    attached_documents_count = serializers.IntegerField(
        source="documents.count",
        read_only=True,
    )
    linked_goal_ids = serializers.PrimaryKeyRelatedField(
        source="treatment_goals",
        many=True,
        read_only=True,
    )
