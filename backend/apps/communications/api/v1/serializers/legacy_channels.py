from __future__ import annotations

from rest_framework import serializers

from apps.communications.models import CommunicationChannelConfig


class CommunicationChannelConfigSerializer(serializers.ModelSerializer):
    """Contrato legado exposto por ``communications.serializers``."""

    class Meta:
        model = CommunicationChannelConfig
        fields = [
            "channel",
            "provider",
            "is_active",
            "sender",
            "public_identifier",
            "connection_status",
            "last_validated_at",
            "metadata",
            "updated_at",
        ]
        read_only_fields = [
            "provider",
            "connection_status",
            "last_validated_at",
            "updated_at",
        ]

    def validate_metadata(self, value):
        forbidden = {
            "api_key",
            "token",
            "secret",
            "password",
            "access_token",
        }
        if any(str(key).lower() in forbidden for key in value):
            raise serializers.ValidationError(
                "Segredos não podem ser enviados por esta API."
            )
        return value
