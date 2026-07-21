"""Django Unfold para organizações, membros, convites e configurações."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.organizations.models import (
    Organization,
    OrganizationInvitation,
    OrganizationMembership,
    OrganizationSettings,
    ProfessionalProfile,
)


@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    list_display = ("name", "organization_type", "status", "onboarding_status", "created_at")
    list_filter = ("organization_type", "status", "onboarding_status")
    search_fields = ("name", "slug", "email")
    readonly_fields = ("id", "slug", "created_at", "updated_at", "onboarding_completed_at")


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(ModelAdmin):
    list_display = ("organization", "user", "role", "status", "is_default")
    list_filter = ("role", "status", "is_default")
    search_fields = ("organization__name", "user__full_name", "user__email")
    autocomplete_fields = ("organization", "user", "invited_by")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(ModelAdmin):
    list_display = ("organization", "email", "role", "status", "expires_at")
    list_filter = ("role", "status")
    search_fields = ("organization__name", "email")
    exclude = ("token_hash",)
    readonly_fields = ("id", "accepted_at", "revoked_at", "created_at", "updated_at")


@admin.register(ProfessionalProfile)
class ProfessionalProfileAdmin(ModelAdmin):
    list_display = ("membership", "display_name", "professional_title", "is_public")
    list_filter = ("is_public", "accepts_online", "accepts_in_person")
    search_fields = ("display_name", "membership__user__email", "council_number")


@admin.register(OrganizationSettings)
class OrganizationSettingsAdmin(ModelAdmin):
    list_display = ("organization", "default_timezone", "default_currency", "allow_online_booking")
    search_fields = ("organization__name",)
