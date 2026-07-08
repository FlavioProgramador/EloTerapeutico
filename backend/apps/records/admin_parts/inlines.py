"""Inlines do admin de prontuários."""

from unfold.admin import TabularInline

from ..models import EvolutionAddendum


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
