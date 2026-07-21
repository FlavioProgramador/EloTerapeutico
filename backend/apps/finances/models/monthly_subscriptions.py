"""Modelo histórico de mensalidades recorrentes de pacientes."""

from __future__ import annotations

from calendar import monthrange
from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .financial_transactions import FinancialTransaction


class MonthlySubscription(models.Model):
    """Acordo recorrente de atendimento e cobrança de um paciente no tenant."""

    class Status(models.TextChoices):
        ACTIVE = "active", _("Ativa")
        PAUSED = "paused", _("Pausada")
        ENDED = "ended", _("Encerrada")
        CANCELLED = "cancelled", _("Cancelada")

    class Frequency(models.TextChoices):
        WEEKLY = "weekly", _("Semanal")
        BIWEEKLY = "biweekly", _("Quinzenal")
        MONTHLY = "monthly", _("Mensal")

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="monthly_subscriptions",
        verbose_name=_("Organização"),
        db_index=True,
    )
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
            models.Index(fields=["organization", "status"], name="fin_sub_org_status_idx"),
            models.Index(
                fields=["organization", "next_billing_date"],
                name="fin_sub_org_bill_idx",
            ),
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
        if self.patient_id and self.patient.organization_id != self.organization_id:
            raise ValidationError({"patient": _("O paciente pertence a outra organização.")})
        if self.patient_id and self.therapist_id and self.patient.therapist_id != self.therapist_id:
            raise ValidationError({"patient": _("O paciente não pertence ao profissional informado.")})
        if self.end_date and self.end_date < self.first_appointment_date:
            raise ValidationError({"end_date": _("A data final deve ser posterior ao primeiro atendimento.")})

    def save(self, *args, **kwargs):
        if not self.next_billing_date:
            self.next_billing_date = self.first_due_date or self.default_first_due_date()
        self.full_clean()
        return super().save(*args, **kwargs)

    def default_first_due_date(self, *, today: date | None = None) -> date:
        reference = today or timezone.localdate()
        year, month = reference.year, reference.month
        candidate = date(year, month, min(self.due_day, monthrange(year, month)[1]))
        if candidate < reference:
            month = 1 if month == 12 else month + 1
            year = year + 1 if month == 1 else year
            candidate = date(year, month, min(self.due_day, monthrange(year, month)[1]))
        return candidate

    def next_billing_date_after(self, current: date | None = None) -> date:
        reference = current or self.next_billing_date or self.default_first_due_date()
        month = 1 if reference.month == 12 else reference.month + 1
        year = reference.year + 1 if month == 1 else reference.year
        return date(year, month, min(self.due_day, monthrange(year, month)[1]))
