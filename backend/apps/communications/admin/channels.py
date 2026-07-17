from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.communications.models import (
    CommunicationChannelConfig,
    CommunicationPlanEntitlement,
)


@admin.register(CommunicationChannelConfig)
class CommunicationChannelConfigAdmin(ModelAdmin):
    list_display = (
        "owner",
        "channel",
        "provider",
        "is_active",
        "connection_status",
        "credential_summary",
        "last_tested_at",
        "last_validated_at",
    )
    list_filter = ("channel", "provider", "is_active", "connection_status")
    search_fields = (
        "owner__email",
        "sender",
        "public_identifier",
        "last_error_code",
    )
    readonly_fields = (
        "credential_summary",
        "last_tested_at",
        "last_validated_at",
        "last_error_code",
        "last_error_message",
        "created_at",
        "updated_at",
    )
    exclude = ("credentials",)
    list_select_related = ("owner",)

    @admin.display(description="Credenciais")
    def credential_summary(self, obj):
        configured = sorted(
            key for key, value in obj.get_credentials().items() if value
        )
        return ", ".join(configured) if configured else "Nenhum segredo armazenado"


@admin.register(CommunicationPlanEntitlement)
class CommunicationPlanEntitlementAdmin(ModelAdmin):
    list_display = (
        "plan",
        "communications_enabled",
        "email_enabled",
        "automations_enabled",
        "max_communications_per_month",
        "max_automations",
    )
    list_filter = (
        "communications_enabled",
        "email_enabled",
        "automations_enabled",
        "whatsapp_enabled",
        "sms_enabled",
    )
    search_fields = ("plan__name", "plan__slug")
    list_select_related = ("plan",)
