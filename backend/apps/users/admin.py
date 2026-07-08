from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from unfold.admin import ModelAdmin

from .models import User, WorkingHours


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = [
        "email",
        "full_name",
        "role",
        "crp_number",
        "is_active",
        "is_staff",
        "locked_status",
        "date_joined",
    ]
    list_filter = ["role", "is_active", "is_staff", "is_superuser", "date_joined"]
    search_fields = ["email", "full_name", "crp_number", "phone"]
    ordering = ["full_name"]
    readonly_fields = ["date_joined", "last_login", "failed_login_attempts", "locked_until"]
    actions = ["action_activate_users", "action_deactivate_users", "action_unlock_users"]

    fieldsets = (
        ("Credenciais", {"fields": ("email", "password")}),
        ("Dados pessoais", {"fields": ("full_name", "phone", "avatar", "bio")}),
        ("Perfil profissional", {"fields": ("role", "specialty", "crp_number")}),
        (
            "Configurações de agenda",
            {"fields": ("default_session_duration", "default_session_value")},
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
