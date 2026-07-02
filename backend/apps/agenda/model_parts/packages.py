from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class PatientPackage(models.Model):
    """Pacote comercial de sessões de um paciente."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Ativo"
        PAUSED = "paused", "Pausado"
        COMPLETED = "completed", "Concluído"
        EXPIRED = "expired", "Expirado"
        CANCELLED = "cancelled", "Cancelado"

    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.PROTECT, related_name="session_packages"
    )
    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="session_packages",
        limit_choices_to={"role": "therapist"},
    )
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    sessions_contracted = models.PositiveIntegerField()
    sessions_used = models.PositiveIntegerField(default=0)
    total_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valid_from = models.DateField(default=timezone.localdate)
    valid_until = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    generate_charge = models.BooleanField(default=False)
    send_charge = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_session_packages",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["therapist", "status"], name="pkg_owner_status_idx"),
            models.Index(fields=["patient", "status"], name="pkg_patient_status_idx"),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def remaining_sessions(self) -> int:
        return max(self.sessions_contracted - self.sessions_used, 0)

    @property
    def unit_value(self) -> Decimal:
        if not self.sessions_contracted:
            return Decimal("0.00")
        return self.total_value / self.sessions_contracted

    @property
    def is_expired(self) -> bool:
        return bool(self.valid_until and self.valid_until < timezone.localdate())

    def can_consume(self) -> bool:
        return (
            self.status == self.Status.ACTIVE
            and not self.is_expired
            and self.remaining_sessions > 0
        )

    def consume(self) -> None:
        with transaction.atomic():
            locked = type(self).objects.select_for_update().get(pk=self.pk)
            if not locked.can_consume():
                raise ValidationError("O pacote não possui saldo disponível.")
            locked.sessions_used += 1
            if locked.sessions_used >= locked.sessions_contracted:
                locked.status = self.Status.COMPLETED
            locked.save(update_fields=["sessions_used", "status", "updated_at"])
            self.sessions_used = locked.sessions_used
            self.status = locked.status

    def release(self) -> None:
        with transaction.atomic():
            locked = type(self).objects.select_for_update().get(pk=self.pk)
            locked.sessions_used = max(locked.sessions_used - 1, 0)
            if locked.status == self.Status.COMPLETED and locked.remaining_sessions > 0:
                locked.status = self.Status.ACTIVE
            locked.save(update_fields=["sessions_used", "status", "updated_at"])
            self.sessions_used = locked.sessions_used
            self.status = locked.status
