"""Admin de aditivos de evolução."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from ..models import EvolutionAddendum


@admin.register(EvolutionAddendum)
class EvolutionAddendumAdmin(ModelAdmin):
    """Admin dos Aditivos de Evolução. Aditivos são imutáveis após criação."""

    list_display = ("id", "evolution", "created_by", "created_at")
    list_filter = ("created_at",)
    search_fields = ("evolution__patient__full_name", "created_by__full_name", "reason")
    readonly_fields = ("evolution", "created_by", "created_at")
    list_select_related = ("evolution__patient", "created_by")

    fieldsets = (
        (
            "Vínculo",
            {"fields": ("evolution", "created_by", "created_at")},
        ),
        (
            "Conteúdo sensível",
            {
                "fields": ("reason", "content"),
                "description": "Dado clínico sensível criptografado.",
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("evolution__patient", "created_by")

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
