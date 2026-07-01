"""
apps/records/admin.py
Configuração do Django Admin para o app de Prontuários.

ATENÇÃO: Campos EncryptedTextField são intencionalmente excluídos do list_display
para evitar descriptografia em massa no admin (performance + segurança).
Eles ficam disponíveis no formulário de edição individual.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Anamnesis, Evolution, EvolutionAddendum

# ─────────────────────────────────────────────────────────────────────────────
# Inline para aditivos dentro da evolução
# ─────────────────────────────────────────────────────────────────────────────


class EvolutionAddendumInline(admin.TabularInline):
    """Exibe aditivos diretamente na tela de edição da evolução."""

    model = EvolutionAddendum
    extra = 0
    fields = ("reason", "created_by", "created_at")
    readonly_fields = ("created_by", "created_at")

    def has_change_permission(self, request, obj=None):
        """Aditivos são imutáveis após criação."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Aditivos não podem ser deletados pelo admin."""
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Anamnesis
# ─────────────────────────────────────────────────────────────────────────────


@admin.register(Anamnesis)
class AnamnesisAdmin(admin.ModelAdmin):
    """
    Admin da Anamnese.
    Campos criptografados (chief_complaint, history, etc.) ficam disponíveis
    apenas no formulário de edição, nunca em listagens.
    """

    # Apenas metadados na listagem — sem descriptografia em massa
    list_display = ("patient", "created_by", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("patient__full_name", "created_by__full_name")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"

    # Organiza os campos no formulário por seção
    fieldsets = (
        (
            "Identificação",
            {
                "fields": ("patient", "created_by"),
            },
        ),
        (
            "Conteúdo Clínico",
            {
                "fields": (
                    "chief_complaint",
                    "history",
                    "medications",
                    "family_history",
                    "observations",
                ),
                "description": (
                    "⚠️ Os campos abaixo contêm dados clínicos sensíveis criptografados. "
                    "Todo acesso é registrado no log de auditoria."
                ),
            },
        ),
        (
            "Metadados",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("patient", "created_by")


# ─────────────────────────────────────────────────────────────────────────────
# Evolution
# ─────────────────────────────────────────────────────────────────────────────


@admin.register(Evolution)
class EvolutionAdmin(admin.ModelAdmin):
    """
    Admin da Evolução de Sessão.

    O campo `content` (criptografado) está disponível somente no formulário
    individual, nunca na listagem, para evitar descriptografia em massa.
    """

    # Apenas metadados na listagem
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
    search_fields = ("patient__full_name", "cid10", "created_by__full_name")
    readonly_fields = ("is_locked", "locked_at", "created_at", "updated_at")
    date_hierarchy = "session_date"
    inlines = [EvolutionAddendumInline]

    fieldsets = (
        (
            "Identificação",
            {
                "fields": ("patient", "appointment", "session_date", "cid10"),
            },
        ),
        (
            "Conteúdo da Sessão",
            {
                "fields": ("content",),
                "description": (
                    "⚠️ Dado clínico sensível criptografado. Acesso registrado em auditoria."
                ),
            },
        ),
        (
            "Controle de Bloqueio",
            {
                "fields": ("is_locked", "locked_at"),
                "classes": ("collapse",),
            },
        ),
        (
            "Autoria",
            {
                "fields": ("created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Status", boolean=False)
    def status_badge(self, obj: Evolution) -> str:
        """Exibe um badge colorido indicando se a evolução está bloqueada ou editável."""
        if obj.is_locked:
            return format_html(
                '<span style="color:#c0392b; font-weight:bold;">🔒 Bloqueada</span>'
            )
        if obj.can_be_edited():
            return format_html(
                '<span style="color:#27ae60; font-weight:bold;">✏️ Editável</span>'
            )
        return format_html(
            '<span style="color:#e67e22; font-weight:bold;">⏳ Pendente bloqueio</span>'
        )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("patient", "created_by", "appointment")
        )

    def has_delete_permission(self, request, obj=None):
        """
        Evoluções não podem ser deletadas via admin — apenas por processo
        administrativo formal (ex: judicial). Retorna False para todos.
        """
        return False


# ─────────────────────────────────────────────────────────────────────────────
# EvolutionAddendum
# ─────────────────────────────────────────────────────────────────────────────


@admin.register(EvolutionAddendum)
class EvolutionAddendumAdmin(admin.ModelAdmin):
    """
    Admin dos Aditivos de Evolução.
    Aditivos são imutáveis após criação.
    """

    list_display = ("id", "evolution", "created_by", "created_at")
    list_filter = ("created_at",)
    search_fields = ("evolution__patient__full_name", "created_by__full_name", "reason")
    readonly_fields = ("evolution", "created_by", "created_at")

    fieldsets = (
        (
            "Vínculo",
            {
                "fields": ("evolution", "created_by", "created_at"),
            },
        ),
        (
            "Conteúdo",
            {
                "fields": ("reason", "content"),
                "description": "⚠️ Dado clínico sensível criptografado.",
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("evolution__patient", "created_by")
        )

    def has_change_permission(self, request, obj=None):
        """Aditivos são imutáveis após criação."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Aditivos não podem ser deletados."""
        return False
