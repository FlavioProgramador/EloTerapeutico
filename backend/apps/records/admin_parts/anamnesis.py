"""Admin da anamnese clínica."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from ..models import Anamnesis


@admin.register(Anamnesis)
class AnamnesisAdmin(ModelAdmin):
    """Admin da Anamnese com cuidado extra para campos clínicos sensíveis."""

    list_display = ("patient", "created_by", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("patient__full_name", "created_by__full_name", "created_by__email")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_select_related = ("patient", "created_by")
    autocomplete_fields = ("patient", "created_by")

    fieldsets = (
        (
            "Identificação",
            {"fields": ("patient", "created_by")},
        ),
        (
            "Conteúdo clínico sensível",
            {
                "fields": (
                    "chief_complaint",
                    "history",
                    "medications",
                    "family_history",
                    "observations",
                ),
                "description": (
                    "Campos clínicos criptografados. Evite abrir ou editar sem necessidade " "operacional legítima."
                ),
            },
        ),
        (
            "Auditoria",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("patient", "created_by")
