"""Backoffice restrito da fundação multi-tenant."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.users.models import Clinic, ClinicInvitation, ClinicMembership


@admin.register(Clinic)
class ClinicAdmin(ModelAdmin):
    list_display = ["public_id", "name", "status", "timezone", "created_at"]
    list_filter = ["status", "timezone", "created_at"]
    search_fields = ["public_id", "name", "legal_name"]
    ordering = ["name", "id"]
    readonly_fields = ["public_id", "created_at", "updated_at"]
    exclude = ["document"]

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ClinicMembership)
class ClinicMembershipAdmin(ModelAdmin):
    list_display = [
        "public_id",
        "clinic",
        "user",
        "role",
        "status",
        "joined_at",
    ]
    list_filter = ["role", "status", "clinic"]
    search_fields = [
        "public_id",
        "clinic__public_id",
        "clinic__name",
        "user__email",
    ]
    list_select_related = ["clinic", "user", "invited_by"]
    autocomplete_fields = ["clinic", "user", "invited_by"]
    readonly_fields = ["public_id", "created_at", "updated_at", "joined_at"]
    exclude = ["extra_permissions"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ClinicInvitation)
class ClinicInvitationAdmin(ModelAdmin):
    list_display = [
        "public_id",
        "clinic",
        "masked_email",
        "role",
        "status",
        "expires_at",
        "created_at",
    ]
    list_filter = ["role", "status", "clinic", "expires_at"]
    search_fields = ["public_id", "clinic__public_id", "clinic__name"]
    list_select_related = ["clinic", "invited_by", "accepted_by"]
    ordering = ["-created_at"]
    readonly_fields = [
        "public_id",
        "clinic",
        "role",
        "status",
        "expires_at",
        "invited_by",
        "accepted_by",
        "accepted_at",
        "created_at",
        "updated_at",
    ]
    exclude = ["email", "token_hash"]

    @admin.display(description="E-mail")
    def masked_email(self, obj):
        local, _, domain = obj.email.partition("@")
        prefix = local[:2] if local else ""
        return f"{prefix}***@{domain}" if domain else "***"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
