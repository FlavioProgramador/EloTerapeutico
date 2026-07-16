"""Backoffice restrito dos documentos clínicos em quarentena."""

from django.conf import settings
from django.contrib import admin, messages
from unfold.admin import ModelAdmin

from apps.audit.services.access_logging import AuditLog, log_access
from apps.records.tasks import scan_clinical_document
from apps.records.treatment_models import ClinicalDocument


@admin.register(ClinicalDocument)
class ClinicalDocumentAdmin(ModelAdmin):
    list_display = [
        "id",
        "patient_id",
        "category",
        "scan_status",
        "scan_attempts",
        "created_at",
        "scanned_at",
    ]
    list_filter = ["scan_status", "category", "is_archived", "created_at"]
    search_fields = ["id", "patient__id", "checksum"]
    list_select_related = ["patient", "uploaded_by", "evolution"]
    ordering = ["-created_at"]
    readonly_fields = [
        "patient",
        "evolution",
        "category",
        "file",
        "quarantine_file",
        "original_name",
        "content_type",
        "size_bytes",
        "checksum",
        "version",
        "is_archived",
        "deleted_at",
        "scan_status",
        "scan_attempts",
        "scan_error_code",
        "scan_started_at",
        "scanned_at",
        "uploaded_by",
        "created_at",
        "updated_at",
    ]
    exclude = ["description"]
    actions = ["retry_security_scan"]

    @admin.action(description="Reprocessar análise de segurança")
    def retry_security_scan(self, request, queryset):
        if not request.user.has_perm("records.change_clinicaldocument"):
            self.message_user(request, "Permissão insuficiente.", messages.ERROR)
            return

        max_attempts = max(int(getattr(settings, "CLINICAL_SCAN_MAX_ATTEMPTS", 3)), 1)
        eligible = queryset.filter(
            scan_status__in=[
                ClinicalDocument.ScanStatus.PENDING,
                ClinicalDocument.ScanStatus.FAILED,
            ],
            scan_attempts__lt=max_attempts,
            quarantine_file__isnull=False,
        )
        scheduled = 0
        for document in eligible.iterator():
            scan_clinical_document.apply_async(args=[document.pk], queue="uploads")
            log_access(
                request,
                AuditLog.Action.UPDATE,
                obj=document,
                obj_repr=f"Documento clínico #{document.pk}:scan_retry",
            )
            scheduled += 1

        self.message_user(
            request,
            f"{scheduled} documento(s) enviado(s) para nova análise.",
            messages.SUCCESS if scheduled else messages.WARNING,
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm("records.change_clinicaldocument")

    def has_delete_permission(self, request, obj=None):
        return False
