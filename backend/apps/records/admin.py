"""
apps/records/admin.py
Configuração do Django Admin para o app de Prontuários.

ATENÇÃO: Campos EncryptedTextField são intencionalmente excluídos do list_display
para evitar descriptografia em massa no admin (performance + segurança).
Eles ficam disponíveis no formulário de edição individual.
"""

from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from .models import Anamnesis, Evolution, EvolutionAddendum


class EvolutionAddendumInline(TabularInline):
    """Exibe aditivos diretamente na tela de edição da evolução."""

    model = EvolutionAddendum
    extra = 0
    fields = ("reason", "created_by", "created_at")
    readonly_fields = ("created_by", "created_at")

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
                    "Campos clínicos criptografados. Evite abrir ou editar sem necessidade "
                    "operacional legítima."
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
