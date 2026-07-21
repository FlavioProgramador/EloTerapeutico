from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Room(models.Model):
    """Sala física pertencente a uma organização."""

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="agenda_rooms",
    )
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
                fields=["organization", "name"],
                name="uniq_room_org_name",
            )
        ]
        indexes = [
            models.Index(fields=["organization", "is_active"], name="room_org_active_idx"),
        ]

    def clean(self):
        super().clean()
        if not self.organization_id or not self.therapist_id:
            return
        from apps.organizations.models import OrganizationMembership

        if not OrganizationMembership.objects.filter(
            organization_id=self.organization_id,
            user_id=self.therapist_id,
            status=OrganizationMembership.Status.ACTIVE,
        ).exists():
            raise ValidationError({"therapist": "O responsável não pertence à organização."})

    def __str__(self) -> str:
        return self.name


class AppointmentRecurrence(models.Model):
    """Regra persistida de uma série de consultas no tenant ativo."""

    class Frequency(models.TextChoices):
        WEEKLY = "weekly", "Semanal"
        BIWEEKLY = "biweekly", "Quinzenal"
        MONTHLY = "monthly", "Mensal"
        CUSTOM = "custom", "Personalizada"

    class Status(models.TextChoices):
        ACTIVE = "active", "Ativa"
        PAUSED = "paused", "Pausada"
        ENDED = "ended", "Encerrada"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="appointment_recurrences",
    )
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="appointment_recurrences")
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
            models.Index(fields=["organization", "status"], name="rec_org_status_idx"),
            models.Index(fields=["therapist", "status"], name="rec_owner_status_idx"),
            models.Index(fields=["patient", "status"], name="rec_patient_status_idx"),
        ]

    def clean(self):
        super().clean()
        if self.patient_id and self.organization_id != self.patient.organization_id:
            raise ValidationError({"patient": "O paciente pertence a outra organização."})
        room = self.room if self.room_id else None
        if room is not None and self.organization_id != room.organization_id:
            raise ValidationError({"room": "A sala pertence a outra organização."})

    def __str__(self) -> str:
        return f"{self.patient} - {self.get_frequency_display()}"
