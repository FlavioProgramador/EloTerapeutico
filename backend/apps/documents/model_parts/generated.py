"""Modelos de documentos gerados."""

from __future__ import annotations

import hashlib
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from core.fields import EncryptedTextField

from .paths import generated_document_path
from .templates import DocumentTemplate


class GeneratedDocument(models.Model):
    """Snapshot imutável do template e dos dados usados para gerar um documento."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        PROCESSING = "processing", "Processando"
        COMPLETED = "completed", "Concluído"
        FAILED = "failed", "Falhou"
        CANCELLED = "cancelled", "Cancelado"
        ARCHIVED = "archived", "Arquivado"

    public_id = models.UUIDField(default=uuid4, unique=True, editable=False, db_index=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="generated_documents",
    )
    professional = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="documents_issued",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="generated_documents",
    )
    template = models.ForeignKey(
        DocumentTemplate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="generated_documents",
    )
    title = models.CharField(max_length=200)
    document_type = models.CharField(
        max_length=32,
        choices=DocumentTemplate.DocumentType.choices,
        default=DocumentTemplate.DocumentType.OTHER,
        db_index=True,
    )
    category = models.CharField(max_length=100, db_index=True)
    document_number = models.CharField(max_length=32)
    template_name_snapshot = models.CharField(max_length=160)
    template_version_snapshot = models.PositiveIntegerField(default=1)
    template_content_snapshot = EncryptedTextField()
    template_header_snapshot = EncryptedTextField(blank=True, default="")
    template_footer_snapshot = EncryptedTextField(blank=True, default="")
    include_professional_identification_snapshot = models.BooleanField(default=True)
    include_clinic_identification_snapshot = models.BooleanField(default=True)
    requires_signature_snapshot = models.BooleanField(default=True)
    rendered_content = EncryptedTextField()
    context_snapshot = EncryptedTextField(default="{}")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    pdf_file = models.FileField(
        upload_to=generated_document_path,
        null=True,
        blank=True,
    )
    pdf_hash = models.CharField(max_length=64, blank=True, db_index=True)
    signature_hash = models.CharField(max_length=64, blank=True)
    professional_name_snapshot = models.CharField(max_length=255)
    professional_registration_snapshot = models.CharField(max_length=50, blank=True)
    failure_reason = models.CharField(max_length=500, blank=True)
    idempotency_key = models.CharField(max_length=128, null=True, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "status"], name="gen_doc_owner_status_idx"),
            models.Index(fields=["patient", "created_at"], name="gen_doc_patient_date_idx"),
            models.Index(fields=["document_type", "created_at"], name="gen_doc_type_date_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "document_number"],
                name="unique_generated_document_number_owner",
            ),
            models.UniqueConstraint(
                fields=["owner", "idempotency_key"],
                condition=Q(idempotency_key__isnull=False),
                name="unique_generated_document_idempotency_owner",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.document_number} — {self.title}"

    @staticmethod
    def calculate_hash(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    def archive(self) -> None:
        self.status = self.Status.ARCHIVED
        self.archived_at = timezone.now()
        self.save(update_fields=["status", "archived_at", "updated_at"])
