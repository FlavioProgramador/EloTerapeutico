"""Admin de evolução clínica."""

from django.contrib import admin
from django.db.models import Q
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from apps.records.services.evolution_security import has_explicit_records_permission

from ..models import Evolution
from .inlines import EvolutionAddendumInline


@admin.register(Evolution)
class EvolutionAdmin(ModelAdmin):
    """Admin da Evolução de Sessão."""

    list_display = (
        "id",
        "patient",
        "session_date",
        "cid10",
        "is_confidential",
        "status_badge",
        "created_by",
        "created_at",
    )
    list_filter = ("is_confidential", "is_locked", "session_date", "created_at")
    search_fields = (
        "patient__full_name",
        "cid10",
        "created_by__full_name",
        "created_by__email",
    )
    readonly_fields = ("is_locked", "locked_at", "created_at", "updated_at")
    date_hierarchy = "session_date"
    inlines = [EvolutionAddendumInline]
    list_select_related = ("patient", "created_by", "appointment")
    autocomplete_fields = ("patient", "created_by")
    raw_id_fields = ("appointment",)

    fieldsets = (
        (
            "Identificação",
            {
                "fields": (
                    "patient",
                    "appointment",
                    "session_date",
                    "cid10",
                    "is_confidential",
                )
            },
        ),
        (
            "Conteúdo da sessão",
            {
                "fields": ("content",),
                "description": (
                    "Dado clínico sensível criptografado. Acesso deve ocorrer apenas "
                    "quando houver justificativa administrativa."
                ),
            },
        ),
        (
            "Controle de bloqueio",
            {"fields": ("is_locked", "locked_at"), "classes": ("collapse",)},
        ),
        (
            "Autoria e auditoria",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Status", boolean=False)
    def status_badge(self, obj: Evolution) -> str:
        from django.utils.safestring import mark_safe
        if obj.is_locked:
            return mark_safe('<span style="color:#b91c1c;font-weight:bold;">Bloqueada</span>')
        if obj.can_be_edited():
            return mark_safe('<span style="color:#15803d;font-weight:bold;">Editável</span>')
        return mark_safe('<span style="color:#ca8a04;font-weight:bold;">Pendente bloqueio</span>')

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related(
            "patient",
            "created_by",
            "appointment",
        )
        if has_explicit_records_permission(request.user, "view_confidential_evolution"):
            return queryset
        return queryset.filter(
            Q(is_confidential=False) | Q(created_by=request.user)
        )

    def has_delete_permission(self, request, obj=None):
        return False
