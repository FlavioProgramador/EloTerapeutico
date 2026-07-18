"""Administração de templates de documentos."""

from django.contrib import admin, messages
from unfold.admin import ModelAdmin

from apps.documents.models import DocumentTemplate
from apps.documents.services import archive_template


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(ModelAdmin):
    list_display = (
        "name",
        "owner",
        "document_type",
        "specialty",
        "status",
        "is_library_template",
        "usage_count",
        "updated_at",
    )
    list_filter = ("status", "is_library_template", "document_type", "specialty")
    search_fields = ("name", "description", "category", "specialty", "owner__email")
    readonly_fields = ("public_id", "usage_count", "created_at", "updated_at", "archived_at")
    autocomplete_fields = ("owner", "source_library_template", "created_by", "updated_by")
    list_select_related = ("owner", "source_library_template", "created_by", "updated_by")
    actions = ("action_archive_templates",)

    fieldsets = (
        (
            "Identificação",
            {
                "fields": (
                    "public_id",
                    "name",
                    "description",
                    "category",
                    "document_type",
                    "specialty",
                )
            },
        ),
        (
            "Escopo e biblioteca",
            {"fields": ("owner", "is_library_template", "source_library_template", "status")},
        ),
        (
            "Conteúdo sensível",
            {
                "fields": ("content", "header_content", "footer_content"),
                "description": "Conteúdo criptografado. Evite acessar sem necessidade operacional.",
            },
        ),
        (
            "Configurações do documento",
            {
                "fields": (
                    "include_professional_identification",
                    "include_clinic_identification",
                    "requires_signature",
                    "version",
                    "usage_count",
                )
            },
        ),
        (
            "Auditoria",
            {
                "fields": ("created_by", "updated_by", "created_at", "updated_at", "archived_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.action(description="Arquivar templates selecionados")
    def action_archive_templates(self, request, queryset):
        if not request.user.has_perm("documents.change_documenttemplate"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return

        count = 0
        for template in queryset.exclude(status=DocumentTemplate.Status.ARCHIVED):
            archive_template(template=template)
            count += 1
        self.message_user(request, f"{count} template(s) arquivado(s).", messages.WARNING)
