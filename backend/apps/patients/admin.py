"""
apps/patients/admin.py
Configuração do Django Admin para o modelo Patient.

Funcionalidades:
- Listagem com campos informativos e filtros
- Ações de soft delete e restauração em massa
- Visualização de pacientes deletados via filtro customizado
- Proteção contra exclusão permanente acidental
"""

from datetime import date

from django.contrib import admin, messages
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from .models import Patient


class SoftDeletedFilter(admin.SimpleListFilter):
    """Filtro customizado para exibir pacientes ativos ou deletados."""

    title = "Situação no sistema"
    parameter_name = "soft_deleted"

    def lookups(self, request, model_admin):
        return [
            ("active", "Ativos"),
            ("deleted", "Arquivados"),
            ("all", "Todos"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "deleted":
            return Patient.all_objects.filter(deleted_at__isnull=False)
        if self.value() == "all":
            return Patient.all_objects.all()
        return queryset.filter(deleted_at__isnull=True)


class IsMinorFilter(admin.SimpleListFilter):
    """Filtro para exibir apenas pacientes menores de 18 anos."""

    title = "Faixa etária"
    parameter_name = "is_minor"

    def lookups(self, request, model_admin):
        return [
            ("minor", "Menores de 18 anos"),
            ("adult", "Adultos (18+)"),
        ]

    def queryset(self, request, queryset):
        today = date.today()
        try:
            cutoff = today.replace(year=today.year - 18)
        except ValueError:
            cutoff = today.replace(year=today.year - 18, day=28)

        if self.value() == "minor":
            return queryset.filter(birth_date__gt=cutoff)
        if self.value() == "adult":
            return queryset.filter(birth_date__lte=cutoff)
        return queryset


@admin.register(Patient)
class PatientAdmin(ModelAdmin):
    """Admin CRM para pacientes, com foco em LGPD e suporte interno."""

    list_display = [
        "display_name_display",
        "masked_cpf_display",
        "age_display",
        "gender",
        "phone",
        "therapist",
        "status_badge",
        "is_active",
        "created_at",
    ]
    list_filter = [
        SoftDeletedFilter,
        "status",
        "gender",
        "attendance_type",
        "modality",
        "payer_type",
        IsMinorFilter,
        "therapist",
        "created_at",
    ]
    search_fields = [
        "full_name",
        "social_name",
        "cpf",
        "email",
        "phone",
        "whatsapp",
        "therapist__full_name",
        "therapist__email",
    ]
    date_hierarchy = "created_at"
    ordering = ["full_name"]
    list_per_page = 25
    list_select_related = ["therapist"]
    autocomplete_fields = ["therapist"]

    readonly_fields = [
        "created_at",
        "updated_at",
        "deleted_at",
        "formatted_cpf_display",
        "masked_cpf_display",
        "age_display",
        "consent_at",
    ]

    fieldsets = [
        (
            "Dados principais",
            {
                "fields": [
                    "full_name",
                    "social_name",
                    "photo",
                    "cpf",
                    "formatted_cpf_display",
                    "rg",
                    "birth_date",
                    "age_display",
                    "gender",
                    "marital_status",
                    "profession",
                ]
            },
        ),
        (
            "Contato",
            {
                "fields": [
                    "email",
                    "phone",
                    "whatsapp",
                    "social_network",
                    "address",
                ]
            },
        ),
        (
            "Vínculo terapêutico",
            {
                "fields": [
                    "therapist",
                    "status",
                    "attendance_type",
                    "modality",
                    "treatment_start_date",
                    "planned_frequency",
                    "referral_source",
                    "tags",
                ]
            },
        ),
        (
            "Financeiro e convênio",
            {
                "fields": [
                    "payer_type",
                    "insurance_name",
                    "session_value",
                    "financial_responsible_name",
                    "financial_responsible_cpf",
                    "financial_responsible_phone",
                    "financial_responsible_email",
                    "financial_responsible_relationship",
                    "financial_responsible_marital_status",
                    "financial_responsible_naturality",
                    "financial_responsible_occupation",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Responsável legal",
            {
                "fields": [
                    "guardian_name",
                    "guardian_cpf",
                    "guardian_phone",
                    "guardian_email",
                    "guardian_relationship",
                ],
                "classes": ["collapse"],
                "description": "Preencher quando houver responsável legal.",
            },
        ),
        (
            "Emergência e lembretes",
            {
                "fields": [
                    "emergency_contact_name",
                    "emergency_contact_relationship",
                    "emergency_contact_phone",
                    "reminders_enabled",
                    "reminder_recipient",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Consentimento e observações administrativas",
            {
                "fields": ["consent_terms_accepted", "consent_at", "notes"],
                "classes": ["collapse"],
            },
        ),
        (
            "Controle interno",
            {
                "fields": ["is_active", "deleted_at", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    actions = ["action_soft_delete", "action_restore", "action_mark_active", "action_mark_inactive"]

    @admin.action(description="Arquivar pacientes selecionados")
    def action_soft_delete(self, request, queryset):
        if not request.user.has_perm("patients.change_patient"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return

        count = 0
        for patient in queryset.filter(deleted_at__isnull=True):
            patient.soft_delete()
            count += 1
        self.message_user(request, f"{count} paciente(s) arquivado(s).", messages.SUCCESS)

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
        self.message_user(request, f"{count} paciente(s) restaurado(s).", messages.SUCCESS)

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

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def delete_queryset(self, request, queryset):
        if not request.user.is_superuser:
            for patient in queryset:
                patient.soft_delete()
            self.message_user(
                request,
                "Pacientes arquivados por soft delete.",
                messages.WARNING,
            )
        else:
            super().delete_queryset(request, queryset)

    def get_queryset(self, request):
        return Patient.all_objects.all().select_related("therapist")
