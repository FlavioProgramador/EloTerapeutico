"""Admin de evolução clínica."""

from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin

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
        "status_badge",
        "created_by",
        "created_at",
    )
    list_filter = ("is_locked", "session_date", "created_at")
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
            {"fields": ("patient", "appointment", "session_date", "cid10")},
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
        if obj.is_locked:
            return format_html('<span style="color:#b91c1c;font-weight:bold;">Bloqueada</span>')
        if obj.can_be_edited():
            return format_html('<span style="color:#15803d;font-weight:bold;">Editável</span>')
        return format_html('<span style="color:#ca8a04;font-weight:bold;">Pendente bloqueio</span>')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("patient", "created_by", "appointment")

    def has_delete_permission(self, request, obj=None):
        return False
