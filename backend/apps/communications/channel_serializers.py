from __future__ import annotations

from rest_framework import serializers

from .models import CommunicationChannelConfig
from .services.channels import (
    configure_channel,
    get_channel_catalog,
    get_configured_secret_state,
    get_missing_configuration_fields,
)


class CommunicationChannelConfigSerializer(serializers.ModelSerializer):
    secrets = serializers.DictField(
        child=serializers.CharField(allow_blank=True, trim_whitespace=True),
        write_only=True,
        required=False,
    )
    save_as_draft = serializers.BooleanField(write_only=True, required=False, default=False)
    confirm_provider_change = serializers.BooleanField(write_only=True, required=False, default=False)
    credential_state = serializers.SerializerMethodField()
    available_providers = serializers.SerializerMethodField()
    missing_fields = serializers.SerializerMethodField()
    configuration_complete = serializers.SerializerMethodField()
    operational_status = serializers.SerializerMethodField()
    last_error = serializers.SerializerMethodField()

    class Meta:
        model = CommunicationChannelConfig
        fields = [
            "channel",
            "provider",
            "is_active",
            "sender",
            "public_identifier",
            "connection_status",
            "operational_status",
            "last_validated_at",
            "last_tested_at",
            "last_error",
            "metadata",
            "credential_state",
            "available_providers",
            "missing_fields",
            "configuration_complete",
            "secrets",
            "save_as_draft",
            "confirm_provider_change",
            "updated_at",
        ]
        read_only_fields = [
            "channel",
            "is_active",
            "connection_status",
            "operational_status",
            "last_validated_at",
            "last_tested_at",
            "last_error",
            "credential_state",
            "available_providers",
            "missing_fields",
            "configuration_complete",
            "updated_at",
        ]

    def get_credential_state(self, obj):
        return get_configured_secret_state(obj)

    def get_available_providers(self, obj):
        return get_channel_catalog(obj.channel)["providers"]

    def get_missing_fields(self, obj):
        return get_missing_configuration_fields(obj)

    def get_configuration_complete(self, obj):
        return not get_missing_configuration_fields(obj)

    def get_operational_status(self, obj):
        if obj.connection_status in {
            CommunicationChannelConfig.ConnectionStatus.ERROR,
            CommunicationChannelConfig.ConnectionStatus.UNAVAILABLE,
        }:
            return obj.connection_status
        if obj.connection_status == CommunicationChannelConfig.ConnectionStatus.VALIDATING:
            return "validating"
        return "active" if obj.is_active else "inactive"

    def get_last_error(self, obj):
        if not obj.last_error_code and not obj.last_error_message:
            return None
        return {
            "code": obj.last_error_code,
            "message": obj.last_error_message,
        }

    def validate_metadata(self, value):
        forbidden = {"api_key", "token", "secret", "password", "access_token", "auth_token"}
        if any(str(key).lower() in forbidden for key in value):
            raise serializers.ValidationError("Segredos devem ser enviados no campo secrets.")
        return value

    def update(self, instance, validated_data):
        return configure_channel(
            instance,
            provider=validated_data.get("provider", instance.provider),
            metadata=validated_data.get("metadata", instance.metadata),
            secrets=validated_data.get("secrets", {}),
            sender=validated_data.get("sender", instance.sender),
            public_identifier=validated_data.get("public_identifier", instance.public_identifier),
            save_as_draft=validated_data.get("save_as_draft", False),
            confirm_provider_change=validated_data.get("confirm_provider_change", False),
        )
