from __future__ import annotations

from rest_framework import serializers

from apps.communications.models import CommunicationTemplate
from apps.communications.validators import validate_template_text


class CommunicationTemplateSerializer(serializers.ModelSerializer):
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = CommunicationTemplate
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "category",
            "channel",
            "subject_template",
            "body_template",
            "allowed_variables",
            "is_system_template",
            "is_active",
            "is_archived",
            "can_edit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "allowed_variables",
            "is_system_template",
            "created_at",
            "updated_at",
        ]

    def get_can_edit(self, obj):
        request = self.context.get("request")
        return bool(
            request
            and obj.owner_id == request.user.pk
            and not obj.is_system_template
        )

    def validate(self, attrs):
        subject = attrs.get(
            "subject_template",
            getattr(self.instance, "subject_template", ""),
        )
        body = attrs.get(
            "body_template",
            getattr(self.instance, "body_template", ""),
        )
        attrs["allowed_variables"] = validate_template_text(subject, body)
        if self.instance and self.instance.is_system_template:
            raise serializers.ValidationError(
                "Templates do sistema não podem ser editados."
            )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return CommunicationTemplate.objects.create(
            owner=request.user,
            created_by=request.user,
            updated_by=request.user,
            **validated_data,
        )

    def update(self, instance, validated_data):
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)
