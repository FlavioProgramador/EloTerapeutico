"""
apps/agenda/admin.py
Configuração do Django Admin para o app de agenda.

Destaques:
  - Status da consulta exibido com cores distintas (HTML safe).
  - Filtros por status, período e terapeuta.
  - Ações em lote: confirmar e cancelar consultas.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Appointment


# Mapa de cores por status para exibição no admin
STATUS_COLORS = {
    Appointment.Status.SCHEDULED:   ("#2563eb", "⏳"),  # azul
    Appointment.Status.CONFIRMED:   ("#16a34a", "✅"),  # verde
    Appointment.Status.MISSED:      ("#dc2626", "❌"),  # vermelho
    Appointment.Status.CANCELLED:   ("#6b7280", "🚫"),  # cinza
    Appointment.Status.RESCHEDULED: ("#d97706", "🔄"),  # laranja
}


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """
    Interface administrativa para consultas.
    Exibe status colorido e permite ações em lote.
    """

    # ── Listagem ──────────────────────────────────────────────────────────────
    list_display = (
        "id",
        "patient",
        "therapist",
        "start_time",
        "end_time",
        "duration_display",
        "colored_status",
        "session_value",
        "is_recurring",
    )
    list_display_links = ("id", "patient")
    list_select_related = ("patient", "therapist")
    list_per_page = 25

    # ── Filtros laterais ──────────────────────────────────────────────────────
    list_filter = (
        "status",
        "therapist",
        ("start_time", admin.DateFieldListFilter),
        "is_recurring",
        "recurrence_rule",
    )

    # ── Busca ─────────────────────────────────────────────────────────────────
    search_fields = (
        "patient__full_name",
        "therapist__full_name",
        "therapist__email",
        "notes",
    )

    # ── Campos de data para navegação hierárquica ─────────────────────────────
    date_hierarchy = "start_time"

    # ── Ordenação padrão ──────────────────────────────────────────────────────
    ordering = ("-start_time",)

    # ── Campos somente-leitura ────────────────────────────────────────────────
    readonly_fields = (
        "created_at",
        "updated_at",
        "duration_minutes",
        "duration_display",
    )

    # ── Layout do formulário de detalhe ──────────────────────────────────────
    fieldsets = (
        (
            "Informações da Consulta",
            {
                "fields": (
                    "patient",
                    "therapist",
                    ("start_time", "end_time"),
                    ("duration_minutes", "session_value"),
                )
            },
        ),
        (
            "Status e Observações",
            {
                "fields": (
                    "status",
                    "notes",
                    "cancellation_reason",
                )
            },
        ),
        (
            "Recorrência",
            {
                "fields": (
                    "is_recurring",
                    "recurrence_rule",
                    "parent_appointment",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Auditoria",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    # ── Ações em lote ─────────────────────────────────────────────────────────
    actions = ["action_confirmar", "action_cancelar"]

    @admin.action(description="✅ Confirmar consultas selecionadas")
    def action_confirmar(self, request, queryset):
        """Confirma em lote as consultas selecionadas."""
        atualizados = queryset.filter(
            status__in=[Appointment.Status.SCHEDULED]
        ).update(status=Appointment.Status.CONFIRMED)
        self.message_user(request, f"{atualizados} consulta(s) confirmada(s).")

    @admin.action(description="🚫 Cancelar consultas selecionadas")
    def action_cancelar(self, request, queryset):
        """Cancela em lote as consultas selecionadas."""
        atualizados = queryset.exclude(
            status__in=[Appointment.Status.CANCELLED, Appointment.Status.MISSED]
        ).update(status=Appointment.Status.CANCELLED)
        self.message_user(request, f"{atualizados} consulta(s) cancelada(s).")

    # ── Método auxiliar: status colorido ─────────────────────────────────────
    @admin.display(description="Status", ordering="status")
    def colored_status(self, obj):
        """Renderiza o status da consulta com cor e ícone no admin."""
        color, icon = STATUS_COLORS.get(obj.status, ("#374151", "•"))
        return format_html(
            '<span style="color: {}; font-weight: 600;">{} {}</span>',
            color,
            icon,
            obj.get_status_display(),
        )
