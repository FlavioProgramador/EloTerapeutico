"""Campos de leitura adicionais do fluxo de evoluções."""

from rest_framework import serializers


class EvolutionFlowReadFieldsMixin(metaclass=serializers.SerializerMetaclass):
    addenda_count = serializers.SerializerMethodField()
    attached_documents_count = serializers.SerializerMethodField()
    linked_goal_ids = serializers.PrimaryKeyRelatedField(
        source="treatment_goals",
        many=True,
        read_only=True,
    )

    def get_addenda_count(self, obj) -> int:
        count = getattr(obj, "annotated_addenda_count", None)
        if count is not None:
            return count
        return obj.addenda.count()

    def get_attached_documents_count(self, obj) -> int:
        count = getattr(obj, "annotated_docs_count", None)
        if count is not None:
            return count
        return obj.documents.filter(
            deleted_at__isnull=True,
            is_archived=False,
        ).count()
