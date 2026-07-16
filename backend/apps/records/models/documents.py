"""Documentos clínicos anexados ao prontuário."""

import hashlib

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.fields import EncryptedTextField

from .paths import clinical_document_path, clinical_document_quarantine_path


class ClinicalDocument(models.Model):
    class Category(models.TextChoices):
        CONSENT = "consent", "Termo de consentimento"
        REPORT = "report", "Relatório"
        REFERRAL = "referral", "Encaminhamento"
        CERTIFICATE = "certificate", "Atestado"
        ASSESSMENT = "assessment", "Avaliação"
        SCALE = "scale", "Escala ou teste"
        PATIENT_FILE = "patient_file", "Documento do paciente"
        OTHER = "other", "Outro"

    class ScanStatus(models.TextChoices):
        PENDING = "pending", "Aguardando análise"
        SCANNING = "scanning", "Em análise"
        CLEAN = "clean", "Liberado"
        INFECTED = "infected", "Arquivo rejeitado"
        FAILED = "failed", "Falha na análise"

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="clinical_documents",
    )
    evolution = models.ForeignKey(
        "records.Evolution",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
    )
    category = models.CharField(
        max_length=24,
        choices=Category.choices,
        default=Category.OTHER,
        db_index=True,
    )
    file = models.FileField(
        upload_to=clinical_document_path,
        null=True,
        blank=True,
        help_text="Arquivo liberado após análise antimalware.",
    )
    quarantine_file = models.FileField(
        upload_to=clinical_document_quarantine_path,
        null=True,
        blank=True,
        help_text="Arquivo temporário, indisponível para download até a análise.",
    )
    original_name = models.CharField(max_length=255)
    description = EncryptedTextField(blank=True, default="")
    content_type = models.CharField(max_length=120)
    size_bytes = models.PositiveBigIntegerField()
    checksum = models.CharField(max_length=64, db_index=True)
    version = models.PositiveIntegerField(default=1)
    is_archived = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    scan_status = models.CharField(
        max_length=16,
        choices=ScanStatus.choices,
        default=ScanStatus.PENDING,
        db_index=True,
    )
    scan_attempts = models.PositiveSmallIntegerField(default=0)
    scan_error_code = models.CharField(max_length=64, blank=True, default="")
    scan_started_at = models.DateTimeField(null=True, blank=True)
    scanned_at = models.DateTimeField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="clinical_documents_uploaded",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["patient", "is_archived"],
                name="document_patient_archive_idx",
            ),
            models.Index(
                fields=["scan_status", "scan_started_at"],
                name="document_scan_status_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(scan_status="clean", file__isnull=False)
                    | ~models.Q(scan_status="clean")
                ),
                name="clinical_document_clean_has_file",
            )
        ]

    @property
    def is_downloadable(self) -> bool:
        return bool(
            self.scan_status == self.ScanStatus.CLEAN
            and self.file
            and not self.is_archived
            and self.deleted_at is None
        )

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.is_archived = True
        self.save(update_fields=["deleted_at", "is_archived", "updated_at"])

    @staticmethod
    def calculate_checksum(uploaded_file) -> str:
        digest = hashlib.sha256()
        for chunk in uploaded_file.chunks():
            digest.update(chunk)
        uploaded_file.seek(0)
        return digest.hexdigest()
