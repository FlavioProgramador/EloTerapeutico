"""Validação compartilhada para escrita parcial de evoluções."""

from rest_framework import serializers

from ..evolution_security import sanitize_clinical_markdown


def preserve_partial_evolution_content(*, instance, attrs):
    clinical_data = attrs.get("clinical_data", {})
    profile = getattr(instance, "clinical_data", None)
    supplied_content = attrs.get("content")
    supplied_observation = clinical_data.get("therapist_observations")
    existing_content = getattr(instance, "content", "") if instance else ""
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
    if not sanitize_clinical_markdown(source):
        raise serializers.ValidationError(
            {"content": "Informe a evolução ou as anotações clínicas."}
        )
    if supplied_content is None and instance:
        attrs["content"] = existing_content
    if supplied_observation is None and instance:
        clinical_data["therapist_observations"] = existing_observation
    attrs["clinical_data"] = clinical_data
    return attrs
