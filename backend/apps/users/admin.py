from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from unfold.admin import ModelAdmin

from apps.audit.models import AuditLog
from apps.audit.services import log_access

from .models import AuthSession, PracticeSettings, User, WorkingHours
from .services.sessions import revoke_all_user_sessions


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = [
        "email",
        "full_name",
        "role",
        "crp_number",
        "onboarding_status",
        "trial_used_at",
        "is_active",
        "is_staff",
        "locked_status",
        "date_joined",
    ]
    list_filter = [
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
        "terms_accepted_at",
        "trial_used_at",
        "onboarding_completed_at",
        "date_joined",
    ]
    search_fields = ["email", "full_name", "crp_number", "phone", "clinic_name"]
    ordering = ["full_name"]
    readonly_fields = [
        "date_joined",
        "last_login",
        "failed_login_attempts",
        "locked_until",
        "terms_accepted_at",
        "privacy_accepted_at",
        "trial_used_at",
        "onboarding_completed_at",
    ]
    actions = ["action_activate_users", "action_deactivate_users", "action_unlock_users"]

    fieldsets = (
        ("Credenciais", {"fields": ("email", "password")}),
        ("Dados pessoais", {"fields": ("full_name", "display_name", "phone", "avatar", "bio")}),
        (
            "Perfil profissional",
            {
                "fields": (
                    "role",
                    "profession",
                    "specialty",
                    "crp_number",
                    "clinic_name",
                    "professional_address",
                )
            },
        ),
        (
            "Configurações de agenda",
            {"fields": ("default_session_duration", "default_session_value", "default_modality", "timezone", "language", "date_format", "time_format")},
        ),
        (
            "Ciclo de vida da conta",
            {
                "fields": (
                    "terms_accepted_at",
                    "privacy_accepted_at",
                    "trial_used_at",
                    "onboarding_completed_at",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Segurança",
            {
                "fields": ("failed_login_attempts", "locked_until"),
                "classes": ("collapse",),
            },
        ),
        (
            "Permissões",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (
            "Auditoria",
            {"fields": ("date_joined", "last_login"), "classes": ("collapse",)},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "role", "password1", "password2"),
            },
        ),
    )

    @admin.display(description="Bloqueio", boolean=True)
    def locked_status(self, obj):
        return bool(obj.locked_until and obj.locked_until > timezone.now())

    @admin.display(description="Onboarding", boolean=True)
    def onboarding_status(self, obj):
        return obj.onboarding_completed

    def save_model(self, request, obj, form, change):
        password_changed = "password" in form.changed_data
        super().save_model(request, obj, form, change)
        if password_changed:
            revoke_all_user_sessions(user=obj, reason="password_changed_by_admin")
            log_access(
                request,
                AuditLog.Action.UPDATE,
                obj=obj,
                obj_repr=f"users.User#{obj.pk}:password_changed_by_admin",
            )

    @admin.action(description="Ativar usuários selecionados")
    def action_activate_users(self, request, queryset):
        if not request.user.has_perm("users.change_user"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} usuário(s) ativado(s).", messages.SUCCESS)

    @admin.action(description="Desativar usuários selecionados")
    def action_deactivate_users(self, request, queryset):
        if not request.user.has_perm("users.change_user"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return
        queryset = queryset.exclude(pk=request.user.pk)
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} usuário(s) desativado(s).", messages.WARNING)

    @admin.action(description="Desbloquear usuários selecionados")
    def action_unlock_users(self, request, queryset):
        if not request.user.has_perm("users.change_user"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return
        updated = queryset.update(failed_login_attempts=0, locked_until=None)
        self.message_user(request, f"{updated} usuário(s) desbloqueado(s).", messages.SUCCESS)


@admin.register(AuthSession)
class AuthSessionAdmin(ModelAdmin):
    list_display = [
        "public_id",
        "user",
        "created_at",
        "last_seen_at",
        "expires_at",
        "revoked_at",
        "active_status",
    ]
    list_filter = ["created_at", "expires_at", "revoked_at"]
    search_fields = ["public_id", "user__email", "user__full_name"]
    list_select_related = ["user"]
    ordering = ["-last_seen_at"]
    readonly_fields = [
        "public_id",
        "user",
        "user_agent",
        "created_at",
        "last_seen_at",
        "expires_at",
        "revoked_at",
        "revoked_reason",
    ]
    exclude = ["refresh_jti"]

    @admin.display(description="Ativa", boolean=True)
    def active_status(self, obj):
        return obj.is_active

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WorkingHours)
class WorkingHoursAdmin(ModelAdmin):
    list_display = ["therapist", "weekday", "start_time", "end_time", "is_active"]
    list_filter = ["weekday", "is_active"]
    search_fields = ["therapist__full_name", "therapist__email"]
    list_select_related = ["therapist"]
    autocomplete_fields = ["therapist"]
    ordering = ["therapist__full_name", "weekday", "start_time"]

    fieldsets = (
        ("Terapeuta", {"fields": ("therapist",)}),
        ("Horário", {"fields": ("weekday", "start_time", "end_time", "is_active")}),
    )


@admin.register(PracticeSettings)
class PracticeSettingsAdmin(ModelAdmin):
    list_display = ["user", "trade_name", "timezone", "currency", "internal_communications_enabled", "updated_at"]
    search_fields = ["user__email", "user__full_name", "trade_name", "document"]
    list_filter = ["internal_communications_enabled", "reminders_enabled", "allow_overbooking", "quiet_hours_enabled"]
    list_select_related = ["user"]
