from django.contrib import admin, messages
from unfold.admin import ModelAdmin

from .models import DocumentSequence, DocumentTemplate, GeneratedDocument


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
            template.archive()
            count += 1
        self.message_user(request, f"{count} template(s) arquivado(s).", messages.WARNING)


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(ModelAdmin):
    list_display = (
        "document_number",
        "title",
        "patient",
        "professional",
        "status",
        "created_at",
        "generated_at",
    )
    list_filter = ("status", "document_type", "category", "created_at", "generated_at")
    search_fields = (
        "document_number",
        "title",
        "patient__full_name",
        "professional__full_name",
        "owner__email",
    )
    readonly_fields = (
        "public_id",
        "document_number",
        "pdf_hash",
        "signature_hash",
        "created_at",
        "updated_at",
        "generated_at",
        "signed_at",
        "archived_at",
    )
    autocomplete_fields = ("owner", "professional", "patient", "template")
    list_select_related = ("owner", "professional", "patient", "template")
    actions = ("action_archive_documents",)

    fieldsets = (
        (
            "Identificação",
            {
                "fields": (
                    "public_id",
                    "owner",
                    "professional",
                    "patient",
                    "template",
                    "title",
                    "document_number",
                    "document_type",
                    "category",
                    "status",
                )
            },
        ),
        (
            "Snapshot do template",
            {
                "fields": (
                    "template_name_snapshot",
                    "template_version_snapshot",
                    "include_professional_identification_snapshot",
                    "include_clinic_identification_snapshot",
                    "requires_signature_snapshot",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Conteúdo renderizado sensível",
            {
                "fields": (
                    "template_content_snapshot",
                    "template_header_snapshot",
                    "template_footer_snapshot",
                    "rendered_content",
                    "context_snapshot",
                ),
                "classes": ("collapse",),
                "description": "Conteúdo criptografado e dados clínicos devem ser acessados com cautela.",
            },
        ),
        (
            "PDF e assinatura",
            {
                "fields": (
                    "pdf_file",
                    "pdf_hash",
                    "signature_hash",
                    "professional_name_snapshot",
                    "professional_registration_snapshot",
                    "failure_reason",
                    "idempotency_key",
                )
            },
        ),
        (
            "Auditoria",
            {
                "fields": ("created_at", "updated_at", "generated_at", "signed_at", "archived_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.action(description="Arquivar documentos selecionados")
    def action_archive_documents(self, request, queryset):
        if not request.user.has_perm("documents.change_generateddocument"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return

        count = 0
        for document in queryset.exclude(status=GeneratedDocument.Status.ARCHIVED):
            document.archive()
            count += 1
        self.message_user(request, f"{count} documento(s) arquivado(s).", messages.WARNING)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


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
