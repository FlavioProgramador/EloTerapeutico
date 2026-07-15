"""Contratos seguros da API de clínicas, memberships e convites."""

from rest_framework import serializers

from apps.users.models import Clinic, ClinicInvitation, ClinicMembership


class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = [
            "public_id",
            "name",
            "email",
            "phone",
            "timezone",
            "logo",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ClinicMembershipSerializer(serializers.ModelSerializer):
    clinic = ClinicSerializer(read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = ClinicMembership
        fields = [
            "public_id",
            "clinic",
            "role",
            "role_display",
            "status",
            "extra_permissions",
            "joined_at",
            "is_current",
        ]
        read_only_fields = fields

    def get_is_current(self, obj: ClinicMembership) -> bool:
        active_clinic_id = self.context.get("active_clinic_id")
        return bool(active_clinic_id and obj.clinic_id == active_clinic_id)


class ClinicSwitchSerializer(serializers.Serializer):
    clinic_id = serializers.UUIDField()


class ClinicInvitationCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=[
            choice
            for choice in ClinicMembership.Role.choices
            if choice[0] != ClinicMembership.Role.OWNER
        ]
    )
    expires_in_days = serializers.IntegerField(min_value=1, max_value=30, default=7)


class ClinicInvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField(min_length=32, max_length=256, write_only=True)


class ClinicInvitationSerializer(serializers.ModelSerializer):
    clinic_id = serializers.UUIDField(source="clinic.public_id", read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = ClinicInvitation
        fields = [
            "public_id",
            "clinic_id",
            "role",
            "role_display",
            "status",
            "expires_at",
            "created_at",
        ]
        read_only_fields = fields
