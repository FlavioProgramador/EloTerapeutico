from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, WorkingHours


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "full_name", "role", "crp_number", "is_active", "date_joined"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["email", "full_name", "crp_number"]
    ordering = ["full_name"]
    readonly_fields = ["date_joined", "last_login", "failed_login_attempts", "locked_until"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Dados Pessoais", {"fields": ("full_name", "phone", "avatar", "bio")}),
        ("Perfil Profissional", {"fields": ("role", "specialty", "crp_number")}),
        ("Configurações de Agenda", {"fields": ("default_session_duration", "default_session_value")}),
        ("Segurança", {"fields": ("failed_login_attempts", "locked_until")}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Datas", {"fields": ("date_joined", "last_login")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "full_name", "role", "password1", "password2"),
        }),
    )


@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = ["therapist", "weekday", "start_time", "end_time", "is_active"]
    list_filter = ["weekday", "is_active"]
    search_fields = ["therapist__full_name", "therapist__email"]
