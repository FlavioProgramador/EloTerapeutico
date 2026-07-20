"""Django Admin read-only dos eventos de auditoria."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.audit.integrations import AuditReadOnlyAdminMixin
from apps.audit.models import AuditLog
from apps.audit.selectors import audit_logs_accessible_to


@admin.register(AuditLog)
class AuditLogAdmin(AuditReadOnlyAdminMixin, ModelAdmin):
    list_display = [
        "timestamp",
        "user",
        "action",
        "content_type",
        "object_id",
        "object_repr",
        "ip_preview",
    ]
    list_filter = ["action", "timestamp", "content_type"]
    search_fields = [
        "user__email",
        "user__full_name",
        "object_repr",
        "object_id",
        "ip_address",
    ]
    readonly_fields = [field.name for field in AuditLog._meta.fields]
    date_hierarchy = "timestamp"
    list_per_page = 50
    ordering = ["-timestamp"]
    actions = None

    def get_queryset(self, request):
        return audit_logs_accessible_to(user=request.user)

    @admin.display(description="IP")
    def ip_preview(self, obj):
        return str(obj.ip_address or "-")


__all__ = ["AuditLogAdmin"]
