"""Configurações institucionais e operacionais da organização."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models


class OrganizationSettings(models.Model):
    organization = models.OneToOneField(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="settings",
    )
    default_timezone = models.CharField(max_length=64, default="America/Sao_Paulo")
    default_currency = models.CharField(max_length=3, default="BRL")
    default_appointment_duration = models.PositiveSmallIntegerField(default=50)
    minimum_booking_notice_minutes = models.PositiveIntegerField(default=0)
    maximum_booking_days = models.PositiveSmallIntegerField(default=90)
    cancellation_notice_hours = models.PositiveSmallIntegerField(default=24)
    allow_online_booking = models.BooleanField(default=False)
    allow_patient_portal = models.BooleanField(default=False)
    allow_telemedicine = models.BooleanField(default=False)
    send_appointment_reminders = models.BooleanField(default=True)
    reminder_hours_before = models.PositiveSmallIntegerField(default=24)
    business_name_on_documents = models.CharField(max_length=180, blank=True)
    document_header = models.TextField(blank=True)
    document_footer = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configurações da organização"
        verbose_name_plural = "Configurações das organizações"

    def clean(self):
        super().clean()
        if self.default_appointment_duration < 5:
            raise ValidationError(
                {"default_appointment_duration": "A duração mínima é de 5 minutos."}
            )
        if self.maximum_booking_days < 1:
            raise ValidationError(
                {"maximum_booking_days": "A janela de agendamento deve ter ao menos um dia."}
            )
        if self.default_currency:
            self.default_currency = self.default_currency.upper()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Configurações de {self.organization_id}"
