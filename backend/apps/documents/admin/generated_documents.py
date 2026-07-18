"""Administração de documentos gerados."""

from django.contrib import admin, messages
from unfold.admin import ModelAdmin

from apps.documents.models import GeneratedDocument
from apps.documents.services import archive_document


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
            archive_document(document=document)
            count += 1
        self.message_user(request, f"{count} documento(s) arquivado(s).", messages.WARNING)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
