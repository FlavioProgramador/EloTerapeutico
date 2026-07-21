from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class TelemedicineRoom(models.Model):
    """Credenciais não previsíveis e revogáveis isoladas por organização."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        AVAILABLE = "available", "Disponível"
        IN_PROGRESS = "in_progress", "Em andamento"
        FINISHED = "finished", "Finalizada"
        CANCELLED = "cancelled", "Cancelada"
        EXPIRED = "expired", "Expirada"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="telemedicine_rooms",
    )
    appointment = models.OneToOneField("agenda.Appointment", on_delete=models.CASCADE, related_name="telemedicine_room")
    patient_token = models.UUIDField(default=uuid4, unique=True, editable=False)
    professional_token = models.UUIDField(default=uuid4, unique=True, editable=False)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["appointment__start_time"]
        indexes = [models.Index(fields=["organization", "status"], name="telemed_org_status_idx")]

    def clean(self):
        super().clean()
        if self.appointment_id and self.appointment.organization_id != self.organization_id:
            raise ValidationError({"appointment": "A consulta pertence a outra organização."})

    @property
    def is_accessible(self) -> bool:
        return (
            not self.revoked_at
            and self.expires_at > timezone.now()
            and self.status
            not in {
                self.Status.CANCELLED,
                self.Status.FINISHED,
                self.Status.EXPIRED,
            }
        )

    def revoke(self) -> None:
        self.revoked_at = timezone.now()
        self.status = self.Status.CANCELLED
        self.save(update_fields=["revoked_at", "status", "updated_at"])

    def regenerate_tokens(self) -> None:
        self.patient_token = uuid4()
        self.professional_token = uuid4()
        self.revoked_at = None
        self.expires_at = max(
            self.appointment.end_time + timedelta(hours=2),
            timezone.now() + timedelta(hours=2),
        )
        self.status = self.Status.AVAILABLE
        self.save(
            update_fields=[
                "patient_token",
                "professional_token",
                "revoked_at",
                "expires_at",
                "status",
                "updated_at",
            ]
        )


class AppointmentReminder(models.Model):
    """Lembrete administrativo sem conteúdo clínico e com tenant explícito."""

    class Channel(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "E-mail"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        SENT = "sent", "Enviado"
        FAILED = "failed", "Falhou"
        CANCELLED = "cancelled", "Cancelado"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="appointment_reminders",
    )
    appointment = models.ForeignKey("agenda.Appointment", on_delete=models.CASCADE, related_name="reminders")
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.WHATSAPP)
    scheduled_for = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    recipient_masked = models.CharField(max_length=32, blank=True)
    error_message = models.CharField(max_length=255, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_for"]
        indexes = [
            models.Index(fields=["organization", "status", "scheduled_for"], name="reminder_org_status_idx"),
            models.Index(fields=["status", "scheduled_for"], name="reminder_status_time_idx"),
        ]

    def clean(self):
        super().clean()
        if self.appointment_id and self.appointment.organization_id != self.organization_id:
            raise ValidationError({"appointment": "A consulta pertence a outra organização."})
