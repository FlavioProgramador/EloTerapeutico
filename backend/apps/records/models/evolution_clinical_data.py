"""Dados clínicos estruturados da evolução."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from core.fields import EncryptedTextField


class EvolutionClinicalData(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        FINALIZED = "finalized", "Finalizada"
        ARCHIVED = "archived", "Arquivada"

    class Modality(models.TextChoices):
        IN_PERSON = "in_person", "Presencial"
        ONLINE = "online", "Online"
        HYBRID = "hybrid", "Híbrido"

    class AppointmentType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        COUPLE = "couple", "Casal"
        FAMILY = "family", "Familiar"
        GROUP = "group", "Grupo"
        OTHER = "other", "Outro"

    evolution = models.OneToOneField(
        "records.Evolution",
        on_delete=models.PROTECT,
        related_name="clinical_data",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    session_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.PositiveSmallIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(600)],
    )
    modality = models.CharField(
        max_length=20,
        choices=Modality.choices,
        default=Modality.IN_PERSON,
    )
    appointment_type = models.CharField(
        max_length=20,
        choices=AppointmentType.choices,
        default=AppointmentType.INDIVIDUAL,
    )
    emotional_state = EncryptedTextField(blank=True, default="")
    chief_complaint = EncryptedTextField(blank=True, default="")
    patient_report = EncryptedTextField(blank=True, default="")
    therapist_observations = EncryptedTextField(blank=True, default="")
    interventions = EncryptedTextField(blank=True, default="")
    perceived_evolution = EncryptedTextField(blank=True, default="")
    homework = EncryptedTextField(blank=True, default="")
    referrals = EncryptedTextField(blank=True, default="")
    next_steps = EncryptedTextField(blank=True, default="")
    finalized_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="evolution_clinical_data_updated",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def finalize(self):
        self.status = self.Status.FINALIZED
        self.finalized_at = timezone.now()
        self.evolution.lock()
        self.save(update_fields=["status", "finalized_at", "updated_at"])

    def archive(self):
        self.status = self.Status.ARCHIVED
        self.archived_at = timezone.now()
        self.evolution.lock()
        self.save(update_fields=["status", "archived_at", "updated_at"])
