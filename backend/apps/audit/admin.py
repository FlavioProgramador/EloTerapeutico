from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    list_display = ["timestamp", "user", "action", "object_repr", "ip_address"]
    list_filter = ["action", "timestamp", "user"]
    search_fields = ["user__email", "user__full_name", "object_repr", "ip_address"]
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
