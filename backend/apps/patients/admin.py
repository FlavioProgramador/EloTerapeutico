"""Admin CRM do módulo de pacientes."""

from django.contrib import admin, messages
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RangeDateFilter, RelatedDropdownFilter

from apps.patients.models import Patient

from .admin_parts import (
    AppointmentInline,
    EvolutionInline,
    FinancialTransactionInline,
    IsMinorFilter,
    PatientAdminActionsMixin,
    PatientAdminDisplayMixin,
    SoftDeletedFilter,
)


@admin.register(Patient)
class PatientAdmin(PatientAdminActionsMixin, PatientAdminDisplayMixin, ModelAdmin):
    """Admin CRM para pacientes, com foco em LGPD e suporte interno."""

    inlines = [EvolutionInline, AppointmentInline, FinancialTransactionInline]

    list_display = [
        "photo_avatar",
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
        ("status", ChoicesDropdownFilter),
        ("gender", ChoicesDropdownFilter),
        ("attendance_type", ChoicesDropdownFilter),
        ("modality", ChoicesDropdownFilter),
        ("payer_type", ChoicesDropdownFilter),
        IsMinorFilter,
        ("therapist", RelatedDropdownFilter),
        ("created_at", RangeDateFilter),
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

    actions = [
        "action_soft_delete",
        "action_restore",
        "action_mark_active",
        "action_mark_inactive",
    ]

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
        qs = Patient.all_objects.all().select_related("therapist")
        if not request.user.is_superuser:
            qs = qs.filter(therapist=request.user)
        return qs
