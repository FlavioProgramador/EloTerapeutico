"""Serializers da API v1 de organizações."""

from __future__ import annotations

from rest_framework import serializers

from apps.organizations.models import (
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
    OrganizationSettings,
    ProfessionalProfile,
)


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "slug",
            "legal_name",
            "organization_type",
            "document",
            "email",
            "phone",
            "timezone",
            "status",
            "onboarding_status",
            "onboarding_step",
            "onboarding_completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "status",
            "onboarding_status",
            "onboarding_step",
            "onboarding_completed_at",
            "created_at",
            "updated_at",
        ]


class OrganizationCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160)
    legal_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    organization_type = serializers.ChoiceField(
        choices=Organization.Type.choices,
        default=Organization.Type.INDIVIDUAL,
    )
    document = serializers.CharField(max_length=32, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(max_length=24, required=False, allow_blank=True)
    timezone = serializers.CharField(max_length=64, default="America/Sao_Paulo")


class MembershipSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = [
            "id",
            "organization",
            "user_id",
            "user_name",
            "user_email",
            "role",
            "status",
            "is_default",
            "joined_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MembershipCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=OrganizationMembership.Role.choices)


class MembershipUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(
        choices=OrganizationMembership.Role.choices,
        required=False,
    )
    status = serializers.ChoiceField(
        choices=OrganizationMembership.Status.choices,
        required=False,
    )


class InvitationSerializer(serializers.ModelSerializer):
    invited_by_name = serializers.CharField(source="invited_by.full_name", read_only=True)

    class Meta:
        model = OrganizationInvitation
        fields = [
            "id",
            "organization",
            "email",
            "role",
            "status",
            "expires_at",
            "invited_by_name",
            "accepted_at",
            "revoked_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class InvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=OrganizationMembership.Role.choices)


class InvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField(min_length=32, max_length=256)


class OrganizationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationSettings
        exclude = ["organization"]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProfessionalProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalProfile
        exclude = ["membership"]
        read_only_fields = ["id", "created_at", "updated_at"]


class OnboardingUpdateSerializer(serializers.Serializer):
    step = serializers.IntegerField(min_value=1, max_value=6, required=False)
    organization = OrganizationCreateSerializer(required=False)
    settings = OrganizationSettingsSerializer(required=False)
    professional_profile = ProfessionalProfileSerializer(required=False)


class OnboardingCompleteSerializer(serializers.Serializer):
    confirm = serializers.BooleanField()

    def validate_confirm(self, value):
        if value is not True:
            raise serializers.ValidationError("Confirme a conclusão do onboarding.")
        return value
