from __future__ import annotations

from rest_framework import serializers

from apps.communications.models import CommunicationTemplate
from apps.communications.validators import validate_template_text
from apps.organizations.models import OrganizationMembership


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

    def _membership(self):
        request = self.context.get("request")
        organization = getattr(request, "organization", None)
        if request is None or organization is None:
            return None
        return OrganizationMembership.objects.filter(
            user=request.user,
            organization=organization,
            status=OrganizationMembership.Status.ACTIVE,
        ).first()

    def get_can_edit(self, obj):
        request = self.context.get("request")
        membership = self._membership()
        if not request or membership is None or obj.is_system_template:
            return False
        if obj.organization_id != membership.organization_id:
            return False
        if membership.role == OrganizationMembership.Role.THERAPIST:
            return obj.owner_id == request.user.pk
        return membership.role in {
            OrganizationMembership.Role.OWNER,
            OrganizationMembership.Role.ADMIN,
        }

    def validate(self, attrs):
        request = self.context.get("request")
        organization = getattr(request, "organization", None)
        if organization is None:
            raise serializers.ValidationError(
                {"organization": "Selecione uma organização."}
            )
        subject = attrs.get(
            "subject_template",
            getattr(self.instance, "subject_template", ""),
        )
        body = attrs.get(
            "body_template",
            getattr(self.instance, "body_template", ""),
        )
        attrs["allowed_variables"] = validate_template_text(subject, body)
        if self.instance:
            if self.instance.is_system_template:
                raise serializers.ValidationError(
                    "Templates do sistema não podem ser editados."
                )
            if self.instance.organization_id != organization.pk:
                raise serializers.ValidationError(
                    "O template pertence a outra organização."
                )
            if not self.get_can_edit(self.instance):
                raise serializers.ValidationError(
                    "Você não pode editar este template."
                )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return CommunicationTemplate.objects.create(
            organization=request.organization,
            owner=request.user,
            created_by=request.user,
            updated_by=request.user,
            is_system_template=False,
            **validated_data,
        )

    def update(self, instance, validated_data):
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)
