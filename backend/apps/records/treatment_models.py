"""Metas terapêuticas e documentos protegidos do prontuário."""

import hashlib
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from core.fields import EncryptedTextField


def clinical_document_path(instance, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"clinical_documents/{instance.patient_id}/{uuid4().hex}{suffix}"


class TreatmentGoal(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Baixa"
        MEDIUM = "medium", "Média"
        HIGH = "high", "Alta"

    class Status(models.TextChoices):
        ACTIVE = "active", "Em andamento"
        PAUSED = "paused", "Pausada"
        COMPLETED = "completed", "Concluída"
        ARCHIVED = "archived", "Arquivada"

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="treatment_goals",
    )
    title = models.CharField(max_length=180)
    description = EncryptedTextField(blank=True, default="")
    category = models.CharField(max_length=80, blank=True)
    priority = models.CharField(
        max_length=12,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    start_date = models.DateField(default=timezone.localdate)
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    progress = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    strategies = EncryptedTextField(blank=True, default="")
    evaluation_criteria = EncryptedTextField(blank=True, default="")
    observations = EncryptedTextField(blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)
    evolutions = models.ManyToManyField(
        "records.Evolution",
        blank=True,
        related_name="treatment_goals",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="treatment_goals_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["sort_order", "-priority", "created_at"]
        indexes = [
            models.Index(fields=["patient", "status"], name="goal_patient_status_idx")
        ]

    def archive(self):
        self.status = self.Status.ARCHIVED
        self.archived_at = timezone.now()
        self.save(update_fields=["status", "archived_at", "updated_at"])


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
    file = models.FileField(upload_to=clinical_document_path)
    original_name = models.CharField(max_length=255)
    description = EncryptedTextField(blank=True, default="")
    content_type = models.CharField(max_length=120)
    size_bytes = models.PositiveBigIntegerField()
    checksum = models.CharField(max_length=64, db_index=True)
    version = models.PositiveIntegerField(default=1)
    is_archived = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
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
            )
        ]

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
