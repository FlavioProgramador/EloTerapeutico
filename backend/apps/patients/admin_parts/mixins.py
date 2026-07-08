"""Mixins de ações e exibição do admin de pacientes."""

from django.contrib import admin, messages
from django.utils.html import format_html

from ..models import Patient


class PatientAdminActionsMixin:
    @admin.action(description="Arquivar pacientes selecionados")
    def action_soft_delete(self, request, queryset):
        if not request.user.has_perm("patients.change_patient"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return

        count = 0
        for patient in queryset.filter(deleted_at__isnull=True):
            patient.soft_delete()
            count += 1
        self.message_user(
            request,
            f"{count} paciente(s) arquivado(s).",
            messages.SUCCESS,
        )

    @admin.action(description="Restaurar pacientes selecionados")
    def action_restore(self, request, queryset):
        if not request.user.has_perm("patients.change_patient"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return

        count = 0
        for patient in Patient.all_objects.filter(
            pk__in=queryset.values_list("pk", flat=True),
            deleted_at__isnull=False,
        ):
            patient.restore()
            count += 1
        self.message_user(
            request,
            f"{count} paciente(s) restaurado(s).",
            messages.SUCCESS,
        )

    @admin.action(description="Marcar pacientes como ativos")
    def action_mark_active(self, request, queryset):
        if not request.user.has_perm("patients.change_patient"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return

        count = 0
        for patient in queryset:
            patient.activate()
            count += 1
        self.message_user(request, f"{count} paciente(s) ativado(s).", messages.SUCCESS)

    @admin.action(description="Marcar pacientes como inativos")
    def action_mark_inactive(self, request, queryset):
        if not request.user.has_perm("patients.change_patient"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return

        count = 0
        for patient in queryset:
            patient.deactivate()
            count += 1
        self.message_user(request, f"{count} paciente(s) inativado(s).", messages.WARNING)


class PatientAdminDisplayMixin:
    @admin.display(description="Foto")
    def photo_avatar(self, obj: Patient):
        if obj.photo:
            return format_html(
                '<img src="{}" style="width: 28px; height: 28px; border-radius: 9999px; object-fit: cover;" />',
                obj.photo.url,
            )
        initials = obj.display_name[:2].upper() if obj.display_name else "PA"
        return format_html(
            '<div style="width: 28px; height: 28px; border-radius: 9999px; '
            "background-color: #f3f4f6; color: #4b5563; display: flex; "
            "align-items: center; justify-content: center; font-size: 10px; "
            'font-weight: 600; border: 1px solid #e5e7eb;">{}</div>',
            initials,
        )

    @admin.display(description="Paciente", ordering="full_name")
    def display_name_display(self, obj: Patient) -> str:
        return obj.display_name

    @admin.display(description="CPF", ordering="cpf")
    def formatted_cpf_display(self, obj: Patient) -> str:
        return obj.formatted_cpf or "—"

    @admin.display(description="CPF", ordering="cpf")
    def masked_cpf_display(self, obj: Patient) -> str:
        return obj.masked_cpf

    @admin.display(description="Idade")
    def age_display(self, obj: Patient) -> str:
        age = obj.age
        if age is None:
            return "—"
        return f"{age} anos"

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj: Patient) -> str:
        color_map = {
            Patient.Status.ACTIVE: "#15803d",
            Patient.Status.EVALUATION: "#0369a1",
            Patient.Status.WAITING_RETURN: "#ca8a04",
            Patient.Status.DISCHARGED: "#0f766e",
            Patient.Status.INACTIVE: "#6b7280",
            Patient.Status.ARCHIVED: "#7f1d1d",
        }
        color = color_map.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color:{};color:white;padding:2px 8px;'
            'border-radius:999px;font-size:0.85em;">{}</span>',
            color,
            obj.get_status_display(),
        )
