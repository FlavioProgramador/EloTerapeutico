"""Modelos estruturados e versões do prontuário clínico."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from core.fields import EncryptedTextField


class AnamnesisProfile(models.Model):
    anamnesis = models.OneToOneField(
        "records.Anamnesis",
        on_delete=models.PROTECT,
        related_name="profile",
    )
    reason_for_care = EncryptedTextField(blank=True, default="")
    physical_health_history = EncryptedTextField(blank=True, default="")
    mental_health_history = EncryptedTextField(blank=True, default="")
    previous_treatments = EncryptedTextField(blank=True, default="")
    habits_and_routine = EncryptedTextField(blank=True, default="")
    sleep = EncryptedTextField(blank=True, default="")
    nutrition = EncryptedTextField(blank=True, default="")
    family_social_relations = EncryptedTextField(blank=True, default="")
    academic_history = EncryptedTextField(blank=True, default="")
    professional_history = EncryptedTextField(blank=True, default="")
    support_network = EncryptedTextField(blank=True, default="")
    relevant_events = EncryptedTextField(blank=True, default="")
    initial_assessment = EncryptedTextField(blank=True, default="")
    clinical_hypotheses = EncryptedTextField(blank=True, default="")
    custom_fields = EncryptedTextField(blank=True, default="{}")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="anamnesis_profiles_updated",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil ampliado de anamnese"
        verbose_name_plural = "Perfis ampliados de anamnese"


class AnamnesisVersion(models.Model):
    anamnesis = models.ForeignKey(
        "records.Anamnesis",
        on_delete=models.PROTECT,
        related_name="versions",
    )
    version = models.PositiveIntegerField()
    snapshot = EncryptedTextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="anamnesis_versions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["anamnesis", "version"],
                name="unique_anamnesis_version",
            )
        ]


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


class EvolutionVersion(models.Model):
    evolution = models.ForeignKey(
        "records.Evolution",
        on_delete=models.PROTECT,
        related_name="versions",
    )
    version = models.PositiveIntegerField()
    snapshot = EncryptedTextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="evolution_versions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["evolution", "version"],
                name="unique_evolution_version",
            )
        ]
