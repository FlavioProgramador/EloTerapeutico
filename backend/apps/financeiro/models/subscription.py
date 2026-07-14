"""Modelo de mensalidades recorrentes."""

from __future__ import annotations

from calendar import monthrange
from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .transaction import FinancialTransaction


class MonthlySubscription(models.Model):
    """Contrato recorrente de atendimento e cobrança de um paciente."""

    class Status(models.TextChoices):
        ACTIVE = "active", _("Ativa")
        PAUSED = "paused", _("Pausada")
        ENDED = "ended", _("Encerrada")
        CANCELLED = "cancelled", _("Cancelada")

    class Frequency(models.TextChoices):
        WEEKLY = "weekly", _("Semanal")
        BIWEEKLY = "biweekly", _("Quinzenal")
        MONTHLY = "monthly", _("Mensal")

    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="monthly_subscriptions",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="monthly_subscriptions",
    )
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)
    frequency = models.CharField(max_length=15, choices=Frequency.choices, default=Frequency.WEEKLY)
    weekday = models.PositiveSmallIntegerField(help_text=_("0=segunda-feira, 6=domingo"))
    appointment_time = models.TimeField()
    first_appointment_date = models.DateField()
    duration_minutes = models.PositiveSmallIntegerField(default=50)
    timezone = models.CharField(max_length=64, default="America/Sao_Paulo")
    end_date = models.DateField(null=True, blank=True)
    occurrence_limit = models.PositiveIntegerField(null=True, blank=True)

    monthly_amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_day = models.PositiveSmallIntegerField(default=5)
    first_due_date = models.DateField(null=True, blank=True)
    next_billing_date = models.DateField(null=True, blank=True)
    reminder_days_before = models.PositiveSmallIntegerField(null=True, blank=True)
    preferred_payment_method = models.CharField(
        max_length=20,
        choices=FinancialTransaction.PaymentMethod.choices,
        default=FinancialTransaction.PaymentMethod.UNINFORMED,
    )
    payment_link = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["patient__full_name"]
        indexes = [
            models.Index(fields=["therapist", "status"], name="fin_sub_status_idx"),
            models.Index(fields=["therapist", "next_billing_date"], name="fin_sub_next_bill_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(monthly_amount__gt=0), name="fin_sub_amount_positive"),
            models.CheckConstraint(condition=Q(due_day__gte=1, due_day__lte=28), name="fin_sub_due_day_valid"),
            models.CheckConstraint(condition=Q(weekday__gte=0, weekday__lte=6), name="fin_sub_weekday_valid"),
            models.CheckConstraint(condition=Q(duration_minutes__gte=15), name="fin_sub_duration_min"),
        ]

    def __str__(self) -> str:
        return f"{self.patient} – R$ {self.monthly_amount:.2f}"

    def clean(self) -> None:
        super().clean()
        if self.patient_id and self.therapist_id and self.patient.therapist_id != self.therapist_id:
            raise ValidationError({"patient": _("O paciente não pertence ao profissional informado.")})
        if self.end_date and self.end_date < self.first_appointment_date:
            raise ValidationError({"end_date": _("A data final deve ser posterior ao primeiro atendimento.")})

    def save(self, *args, **kwargs):
        if not self.next_billing_date:
            self.next_billing_date = self.first_due_date or self._default_first_due_date()
        self.full_clean()
        return super().save(*args, **kwargs)

    def _default_first_due_date(self) -> date:
        today = timezone.localdate()
        year, month = today.year, today.month
        candidate = date(year, month, min(self.due_day, monthrange(year, month)[1]))
        if candidate < today:
            month = 1 if month == 12 else month + 1
            year = year + 1 if month == 1 else year
            candidate = date(year, month, min(self.due_day, monthrange(year, month)[1]))
        return candidate

    def advance_next_billing_date(self) -> None:
        current = self.next_billing_date or self._default_first_due_date()
        month = 1 if current.month == 12 else current.month + 1
        year = current.year + 1 if month == 1 else current.year
        self.next_billing_date = date(year, month, min(self.due_day, monthrange(year, month)[1]))
        self.save(update_fields=["next_billing_date", "updated_at"])
