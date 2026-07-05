from django.contrib import admin

from .models import DocumentSequence, DocumentTemplate, GeneratedDocument


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
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
    search_fields = ("name", "description", "category", "specialty")
    readonly_fields = ("public_id", "usage_count", "created_at", "updated_at")


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "document_number",
        "title",
        "patient",
        "professional",
        "status",
        "created_at",
        "generated_at",
    )
    list_filter = ("status", "document_type", "category")
    search_fields = ("document_number", "title", "patient__full_name")
    readonly_fields = (
        "public_id",
        "document_number",
        "pdf_hash",
        "signature_hash",
        "created_at",
        "updated_at",
        "generated_at",
    )


@admin.register(DocumentSequence)
class DocumentSequenceAdmin(admin.ModelAdmin):
    list_display = ("owner", "year", "last_value", "updated_at")
    readonly_fields = ("updated_at",)
