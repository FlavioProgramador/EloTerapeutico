from __future__ import annotations

from rest_framework import serializers

from apps.communications.models import InAppNotification, NotificationPreference


class InAppNotificationSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(
        source="get_category_display",
        read_only=True,
    )
    priority_display = serializers.CharField(
        source="get_priority_display",
        read_only=True,
    )

    class Meta:
        model = InAppNotification
        fields = [
            "public_id",
            "category",
            "category_display",
            "title",
            "message",
            "notification_type",
            "priority",
            "priority_display",
            "internal_url",
            "action_label",
            "metadata",
            "is_read",
            "read_at",
            "archived_at",
            "created_at",
            "expires_at",
        ]
        read_only_fields = fields


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            "in_app_enabled",
            "email_enabled",
            "whatsapp_enabled",
            "push_enabled",
            "quiet_hours_enabled",
            "quiet_hours_start",
            "quiet_hours_end",
            "timezone",
            "category_preferences",
            "daily_digest_enabled",
            "updated_at",
        ]
        read_only_fields = ["push_enabled", "updated_at"]

    def validate(self, attrs):
        enabled = attrs.get(
            "quiet_hours_enabled",
            getattr(self.instance, "quiet_hours_enabled", False),
        )
        start = attrs.get(
            "quiet_hours_start",
            getattr(self.instance, "quiet_hours_start", None),
        )
        end = attrs.get(
            "quiet_hours_end",
            getattr(self.instance, "quiet_hours_end", None),
        )
        if enabled and (start is None or end is None):
            raise serializers.ValidationError(
                {
                    "quiet_hours_start": (
                        "Informe o início e o fim do horário de silêncio."
                    )
                }
            )
        return attrs

    def validate_whatsapp_enabled(self, value):
        if value:
            raise serializers.ValidationError(
                "O canal WhatsApp ainda não está configurado para "
                "notificações do sistema."
            )
        return value

    def validate_category_preferences(self, value):
        allowed_categories = set(InAppNotification.Category.values)
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "As preferências por categoria devem ser um objeto."
            )
        clean = {}
        for category, channels in value.items():
            if category not in allowed_categories or not isinstance(channels, dict):
                raise serializers.ValidationError(
                    "Categoria de notificação inválida."
                )
            if channels.get("whatsapp") or channels.get("push"):
                raise serializers.ValidationError(
                    "WhatsApp e push ainda não estão disponíveis para "
                    "notificações."
                )
            clean[category] = {
                "in_app": bool(channels.get("in_app", True)),
                "email": bool(channels.get("email", False)),
                "whatsapp": False,
                "push": False,
            }
        return clean
