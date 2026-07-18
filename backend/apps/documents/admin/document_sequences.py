"""Administração das sequências de numeração documental."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.documents.models import DocumentSequence


@admin.register(DocumentSequence)
class DocumentSequenceAdmin(ModelAdmin):
    list_display = ("owner", "year", "last_value", "updated_at")
    list_filter = ("year",)
    search_fields = ("owner__full_name", "owner__email")
    readonly_fields = ("updated_at",)
    autocomplete_fields = ("owner",)
    list_select_related = ("owner",)

    fieldsets = (
        ("Sequência", {"fields": ("owner", "year", "last_value")}),
        ("Auditoria", {"fields": ("updated_at",), "classes": ("collapse",)}),
    )
