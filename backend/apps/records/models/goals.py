"""Metas terapêuticas do prontuário."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.fields import EncryptedTextField


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
            models.Index(
                fields=["patient", "status"],
                name="goal_patient_status_idx",
            )
        ]

    def archive(self):
        self.status = self.Status.ARCHIVED
        self.archived_at = timezone.now()
        self.save(update_fields=["status", "archived_at", "updated_at"])
