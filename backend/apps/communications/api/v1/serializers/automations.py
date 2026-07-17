from __future__ import annotations

from rest_framework import serializers

from apps.communications.models import (
    CommunicationAutomation,
    CommunicationAutomationRun,
)


class CommunicationAutomationSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True)
    last_run_at = serializers.SerializerMethodField()
    failures = serializers.SerializerMethodField()

    class Meta:
        model = CommunicationAutomation
        fields = [
            "id",
            "name",
            "description",
            "event_type",
            "channel",
            "template",
            "template_name",
            "is_active",
            "delay_value",
            "delay_unit",
            "send_before_event",
            "conditions",
            "allowed_start_time",
            "allowed_end_time",
            "allowed_weekdays",
            "respect_preferences",
            "max_executions",
            "priority",
            "fallback_channel",
            "last_run_at",
            "failures",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["is_active", "created_at", "updated_at"]

    def get_last_run_at(self, obj):
        run = obj.runs.order_by("-started_at").first()
        return run.started_at if run else None

    def get_failures(self, obj):
        return obj.runs.filter(
            status=CommunicationAutomationRun.Status.FAILED
        ).count()

    def validate_template(self, template):
        request = self.context["request"]
        if template.owner_id not in {None, request.user.pk}:
            raise serializers.ValidationError("Template inválido.")
        return template

    def validate(self, attrs):
        template = attrs.get("template", getattr(self.instance, "template", None))
        channel = attrs.get("channel", getattr(self.instance, "channel", None))
        if template and channel and template.channel != channel:
            raise serializers.ValidationError(
                {"template": "O template deve usar o mesmo canal da automação."}
            )
        allowed_operators = {
            "equals",
            "not_equals",
            "contains",
            "greater_than",
            "less_than",
            "is_empty",
            "is_not_empty",
        }
        for condition in attrs.get("conditions", []):
            if (
                not isinstance(condition, dict)
                or condition.get("operator") not in allowed_operators
            ):
                raise serializers.ValidationError(
                    {"conditions": "A lista contém uma condição inválida."}
                )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return CommunicationAutomation.objects.create(
            owner=request.user,
            created_by=request.user,
            updated_by=request.user,
            **validated_data,
        )

    def update(self, instance, validated_data):
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


class CommunicationAutomationRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationAutomationRun
        fields = [
            "id",
            "source_event",
            "source_object_type",
            "source_object_id",
            "status",
            "skip_reason",
            "communication",
            "error_message",
            "started_at",
            "finished_at",
        ]
        read_only_fields = fields
