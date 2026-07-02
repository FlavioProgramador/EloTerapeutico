from __future__ import annotations

from django.conf import settings
from django.db import models


class Room(models.Model):
    """Sala física disponível para atendimentos presenciais."""

    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agenda_rooms",
        verbose_name="Responsável",
    )
    name = models.CharField(max_length=120, verbose_name="Nome")
    location = models.CharField(max_length=255, blank=True, verbose_name="Localização")
    capacity = models.PositiveSmallIntegerField(default=1, verbose_name="Capacidade")
    is_active = models.BooleanField(default=True, verbose_name="Ativa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["therapist", "name"], name="uniq_room_owner_name"
            )
        ]

    def __str__(self) -> str:
        return self.name


class AppointmentRecurrence(models.Model):
    """Regra persistida de uma série de consultas."""

    class Frequency(models.TextChoices):
        WEEKLY = "weekly", "Semanal"
        BIWEEKLY = "biweekly", "Quinzenal"
        MONTHLY = "monthly", "Mensal"
        CUSTOM = "custom", "Personalizada"

    class Status(models.TextChoices):
        ACTIVE = "active", "Ativa"
        PAUSED = "paused", "Pausada"
        ENDED = "ended", "Encerrada"

    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.PROTECT, related_name="appointment_recurrences"
    )
    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="appointment_recurrences",
        limit_choices_to={"role": "therapist"},
    )
    frequency = models.CharField(max_length=20, choices=Frequency.choices)
    interval = models.PositiveSmallIntegerField(default=1)
    weekdays = models.JSONField(default=list, blank=True)
    starts_on = models.DateField()
    ends_on = models.DateField(null=True, blank=True)
    max_occurrences = models.PositiveIntegerField(null=True, blank=True)
    start_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=50)
    timezone_name = models.CharField(max_length=64, default="America/Sao_Paulo")
    modality = models.CharField(max_length=20, default="in_person")
    appointment_type = models.CharField(max_length=30, default="psychotherapy")
    room = models.ForeignKey(
        Room,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recurrences",
    )
    session_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_appointment_recurrences",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["therapist", "status"], name="rec_owner_status_idx"),
            models.Index(fields=["patient", "status"], name="rec_patient_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.patient} - {self.get_frequency_display()}"
