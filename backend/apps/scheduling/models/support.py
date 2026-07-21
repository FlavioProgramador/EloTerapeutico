from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class ScheduleBlock(models.Model):
    """Intervalo indisponível do profissional dentro de uma organização."""

    class Reason(models.TextChoices):
        LUNCH = "lunch", "Almoço"
        MEETING = "meeting", "Reunião"
        VACATION = "vacation", "Férias"
        EXTERNAL = "external", "Atendimento externo"
        APPOINTMENT = "appointment", "Compromisso"
        OTHER = "other", "Outro"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="schedule_blocks",
    )
    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="schedule_blocks",
        limit_choices_to={"role": "therapist"},
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    reason = models.CharField(max_length=20, choices=Reason.choices, default=Reason.OTHER)
    notes = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    recurrence_rule = models.CharField(max_length=20, blank=True)
    parent_block = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="occurrences",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_schedule_blocks",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_time"]
        indexes = [
            models.Index(fields=["organization", "start_time"], name="block_org_start_idx"),
            models.Index(fields=["therapist", "start_time"], name="block_owner_start_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=models.F("start_time")),
                name="block_end_after_start",
            )
        ]

    def __str__(self) -> str:
        return f"Bloqueio {self.start_time:%d/%m/%Y %H:%M}"

    def clean(self):
        super().clean()
        if self.start_time >= self.end_time:
            raise ValidationError({"end_time": "O término deve ser posterior ao início."})
        parent_block = self.parent_block if self.parent_block_id else None
        if parent_block is not None and parent_block.organization_id != self.organization_id:
            raise ValidationError({"parent_block": "O bloqueio-pai pertence a outra organização."})


class PackageSession(models.Model):
    """Vínculo auditável entre sessão e pacote dentro do tenant."""

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Agendada"
        CONFIRMED = "confirmed", "Confirmada"
        COMPLETED = "completed", "Realizada"
        MISSED = "missed", "Falta"
        CANCELLED = "cancelled", "Cancelada"
        RESCHEDULED = "rescheduled", "Remarcada"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="package_sessions",
    )
    package = models.ForeignKey("agenda.PatientPackage", on_delete=models.CASCADE, related_name="package_sessions")
    appointment = models.OneToOneField(
        "agenda.Appointment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="package_session",
    )
    scheduled_for = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    consumed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_for"]
        constraints = [models.UniqueConstraint(fields=["package", "scheduled_for"], name="uniq_pkg_session_datetime")]
        indexes = [models.Index(fields=["organization", "scheduled_for"], name="pkg_session_org_time_idx")]

    def clean(self):
        super().clean()
        if self.package_id and self.package.organization_id != self.organization_id:
            raise ValidationError({"package": "O pacote pertence a outra organização."})
        appointment = self.appointment if self.appointment_id else None
        if appointment is not None and appointment.organization_id != self.organization_id:
            raise ValidationError({"appointment": "A consulta pertence a outra organização."})

    def __str__(self) -> str:
        return f"Sessão {self.package_id} - {self.scheduled_for:%d/%m/%Y}"
