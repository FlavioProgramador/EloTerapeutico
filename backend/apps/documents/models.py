"""Modelos do módulo de templates e documentos gerados."""

from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.fields import EncryptedTextField


def generated_document_path(instance: "GeneratedDocument", filename: str) -> str:
    """Gera um caminho não previsível sem dados pessoais no nome do arquivo."""

    suffix = Path(filename).suffix.lower() or ".pdf"
    return f"generated_documents/{instance.owner_id}/{instance.public_id.hex}{suffix}"


class DocumentTemplate(models.Model):
    """Modelo reutilizável de documento, privado ou pertencente à biblioteca global."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Ativo"
        INACTIVE = "inactive", "Inativo"
        ARCHIVED = "archived", "Arquivado"

    class DocumentType(models.TextChoices):
        DECLARATION = "declaration", "Declaração"
        REPORT = "report", "Relatório"
        REFERRAL = "referral", "Encaminhamento"
        CERTIFICATE = "certificate", "Atestado"
        CONSENT = "consent", "Termo de consentimento"
        OTHER = "other", "Outro"

    public_id = models.UUIDField(default=uuid4, unique=True, editable=False, db_index=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="document_templates",
        help_text="Nulo apenas para templates globais da biblioteca.",
    )
    source_library_template = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="imported_copies",
    )
    name = models.CharField(max_length=160)
    description = models.CharField(max_length=500, blank=True)
    category = models.CharField(max_length=100, db_index=True)
    document_type = models.CharField(
        max_length=32,
        choices=DocumentType.choices,
        default=DocumentType.OTHER,
        db_index=True,
    )
    specialty = models.CharField(max_length=120, blank=True, db_index=True)
    content = EncryptedTextField()
    header_content = EncryptedTextField(blank=True, default="")
    footer_content = EncryptedTextField(blank=True, default="")
    include_professional_identification = models.BooleanField(default=True)
    include_clinic_identification = models.BooleanField(default=True)
    requires_signature = models.BooleanField(default=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    is_library_template = models.BooleanField(default=False, db_index=True)
    version = models.PositiveIntegerField(default=1)
    usage_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="document_templates_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="document_templates_updated",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["owner", "status"], name="doc_tpl_owner_status_idx"),
            models.Index(
                fields=["is_library_template", "specialty"],
                name="doc_tpl_library_spec_idx",
            ),
            models.Index(fields=["document_type", "category"], name="doc_tpl_type_cat_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"],
                condition=Q(archived_at__isnull=True, owner__isnull=False),
                name="unique_active_document_template_owner_name",
            ),
            models.UniqueConstraint(
                fields=["name"],
                condition=Q(
                    owner__isnull=True,
                    is_library_template=True,
                    archived_at__isnull=True,
                ),
                name="unique_active_library_template_name",
            ),
            models.CheckConstraint(
                condition=(
                    Q(is_library_template=False, owner__isnull=False)
                    | Q(is_library_template=True, owner__isnull=True)
                ),
                name="document_template_scope_consistent",
            ),
        ]
        permissions = [
            (
                "manage_document_library",
                "Can manage the global document template library",
            )
        ]

    def __str__(self) -> str:
        scope = "Biblioteca" if self.is_library_template else f"Usuário {self.owner_id}"
        return f"{self.name} ({scope})"

    def archive(self) -> None:
        self.status = self.Status.ARCHIVED
        self.archived_at = timezone.now()
        self.save(update_fields=["status", "archived_at", "updated_at"])


class DocumentSequence(models.Model):
    """Sequência transacional por profissional e ano para numeração documental."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_sequences",
    )
    year = models.PositiveSmallIntegerField()
    last_value = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "year"],
                name="unique_document_sequence_owner_year",
            )
        ]


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
