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
        prefetched = getattr(obj, "_prefetched_objects_cache", {})
        if "addenda" in prefetched:
            return len(prefetched["addenda"])
        return obj.addenda.count()

    def get_attached_documents_count(self, obj) -> int:
        count = getattr(obj, "annotated_docs_count", None)
        if count is not None:
            return count
        active_docs = getattr(obj, "active_documents", None)
        if active_docs is not None:
            return len(active_docs)
        prefetched = getattr(obj, "_prefetched_objects_cache", {})
        if "documents" in prefetched:
            return len(
                [
                    doc
                    for doc in prefetched["documents"]
                    if getattr(doc, "deleted_at", None) is None and not getattr(doc, "is_archived", False)
                ]
            )
        return obj.documents.filter(
            deleted_at__isnull=True,
            is_archived=False,
        ).count()
