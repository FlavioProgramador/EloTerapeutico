"""
apps/patients/admin.py
Configuração do Django Admin para o modelo Patient.

Funcionalidades:
- Listagem com campos informativos e filtros
- Ações de soft delete e restauração em massa
- Visualização de pacientes deletados via filtro customizado
- Proteção contra exclusão permanente acidental
"""

from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html

from .models import Patient


class SoftDeletedFilter(admin.SimpleListFilter):
    """
    Filtro customizado para exibir pacientes ativos ou deletados (soft delete).
    Por padrão, o Admin exibe apenas os ativos.
    """

    title = "Situação no sistema"
    parameter_name = "soft_deleted"

    def lookups(self, request, model_admin):
        return [
            ("active", "Ativos"),
            ("deleted", "Excluídos (soft delete)"),
            ("all", "Todos"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "deleted":
            # Usa all_objects para acessar registros soft-deleted
            return Patient.all_objects.filter(deleted_at__isnull=False)
        if self.value() == "all":
            return Patient.all_objects.all()
        # Padrão: somente ativos (deleted_at=None)
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
        from datetime import date
        from dateutil.relativedelta import relativedelta

        today = date.today()
        cutoff = today - relativedelta(years=18)

        if self.value() == "minor":
            return queryset.filter(birth_date__gt=cutoff)
        if self.value() == "adult":
            return queryset.filter(birth_date__lte=cutoff)
        return queryset


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """
    Admin customizado para o modelo Patient.

    Visibilidade:
    - Superusuários e admins veem todos os pacientes.
    - O filtro de soft-delete está disponível na barra lateral.

    Segurança:
    - O botão "Delete" do Django Admin está desabilitado para
      evitar exclusão permanente. Use a ação "soft_delete" em seu lugar.
    """

    # ── Listagem ─────────────────────────────────────────────────────────────
    list_display = [
        "full_name",
        "formatted_cpf_display",
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
        IsMinorFilter,
        "therapist",
        "created_at",
    ]
    search_fields = [
        "full_name",
        "cpf",
        "email",
        "phone",
        "therapist__full_name",
        "therapist__email",
    ]
    date_hierarchy = "created_at"
    ordering = ["full_name"]
    list_per_page = 25

    # ── Readonly ─────────────────────────────────────────────────────────────
    readonly_fields = [
        "created_at",
        "updated_at",
        "deleted_at",
        "formatted_cpf_display",
        "age_display",
    ]

    # ── Fieldsets para o formulário de detalhe ────────────────────────────────
    fieldsets = [
        (
            "Identificação",
            {
                "fields": [
                    "full_name",
                    "cpf",
                    "birth_date",
                    "gender",
                    "age_display",
                ]
            },
        ),
        (
            "Contato",
            {
                "fields": ["email", "phone"],
            },
        ),
        (
            "Endereço",
            {
                "fields": ["address"],
                "classes": ["collapse"],
            },
        ),
        (
            "Vínculo Terapêutico",
            {
                "fields": ["therapist", "status", "referral_source"],
            },
        ),
        (
            "Responsável Legal",
            {
                "fields": ["guardian_name", "guardian_cpf"],
                "classes": ["collapse"],
                "description": "Preencher apenas para pacientes menores de 18 anos.",
            },
        ),
        (
            "Observações",
            {
                "fields": ["notes"],
                "classes": ["collapse"],
            },
        ),
        (
            "Controle do Sistema",
            {
                "fields": ["is_active", "deleted_at", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    # ── Ações em massa ───────────────────────────────────────────────────────
    actions = ["action_soft_delete", "action_restore"]

    @admin.action(description="🗑️ Desativar pacientes selecionados (soft delete)")
    def action_soft_delete(self, request, queryset):
        """Aplica soft delete em todos os pacientes selecionados."""
        count = 0
        for patient in queryset.filter(deleted_at__isnull=True):
            patient.soft_delete()
            count += 1
        self.message_user(
            request,
            f"{count} paciente(s) desativado(s) com sucesso.",
            messages.SUCCESS,
        )

    @admin.action(description="♻️ Restaurar pacientes selecionados")
    def action_restore(self, request, queryset):
        """
        Restaura pacientes que foram excluídos via soft delete.
        Para acessar pacientes soft-deleted, selecione 'Excluídos' no filtro.
        """
        count = 0
        for patient in Patient.all_objects.filter(
            pk__in=queryset.values_list("pk", flat=True),
            deleted_at__isnull=False,
        ):
            patient.restore()
            count += 1
        self.message_user(
            request,
            f"{count} paciente(s) restaurado(s) com sucesso.",
            messages.SUCCESS,
        )

    # ── Colunas customizadas ─────────────────────────────────────────────────

    @admin.display(description="CPF", ordering="cpf")
    def formatted_cpf_display(self, obj: Patient) -> str:
        """Exibe o CPF formatado na listagem."""
        return obj.formatted_cpf

    @admin.display(description="Idade")
    def age_display(self, obj: Patient) -> str:
        """Exibe a idade do paciente na listagem."""
        age = obj.age
        if age is None:
            return "—"
        return f"{age} anos"

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj: Patient) -> str:
        """Exibe o status com cor de badge HTML."""
        color_map = {
            Patient.Status.ACTIVE: "#28a745",
            Patient.Status.INACTIVE: "#6c757d",
            Patient.Status.DISCHARGED: "#17a2b8",
        }
        color = color_map.get(obj.status, "#6c757d")
        return format_html(
            '<span style="'
            "background-color: {}; color: white; padding: 2px 8px; "
            'border-radius: 4px; font-size: 0.85em;">{}</span>',
            color,
            obj.get_status_display(),
        )

    # ── Proteção contra exclusão permanente ──────────────────────────────────

    def has_delete_permission(self, request, obj=None):
        """
        Desabilita a exclusão permanente via Admin.
        Use a ação 'Desativar (soft delete)' para remover pacientes.
        Apenas superusuários podem excluir permanentemente.
        """
        return request.user.is_superuser

    def delete_queryset(self, request, queryset):
        """Sobrescreve a exclusão em massa para usar soft delete."""
        if not request.user.is_superuser:
            for patient in queryset:
                patient.soft_delete()
            self.message_user(
                request,
                "Pacientes desativados via soft delete (não excluídos permanentemente).",
                messages.WARNING,
            )
        else:
            super().delete_queryset(request, queryset)

    def get_queryset(self, request):
        """
        Admin usa all_objects para que o filtro de soft-deleted funcione.
        Por padrão exibe apenas ativos.
        """
        return Patient.all_objects.all()
