from __future__ import annotations

from django.conf import settings
from django.db import models

from .communication import Communication


class CommunicationPreference(models.Model):
    class PreferredChannel(models.TextChoices):
        EMAIL = Communication.Channel.EMAIL, "E-mail"
        WHATSAPP_MANUAL = Communication.Channel.WHATSAPP_MANUAL, "WhatsApp"
        IN_APP = Communication.Channel.IN_APP, "Notificação interna"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="communication_preferences",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="communication_preferences",
    )
    preferred_channel = models.CharField(
        max_length=24,
        choices=PreferredChannel.choices,
        default=PreferredChannel.EMAIL,
    )
    allow_email = models.BooleanField(default=True)
    allow_whatsapp = models.BooleanField(default=False)
    allow_sms = models.BooleanField(default=False)
    allow_reminders = models.BooleanField(default=True)
    allow_financial_notices = models.BooleanField(default=True)
    allow_form_requests = models.BooleanField(default=True)
    allowed_start_time = models.TimeField(null=True, blank=True)
    allowed_end_time = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=64, default="America/Sao_Paulo")
    general_opt_out = models.BooleanField(default=False)
    opt_out_reason = models.CharField(max_length=255, blank=True)
    opted_out_at = models.DateTimeField(null=True, blank=True)
    consent_source = models.CharField(max_length=80, blank=True)
    consented_at = models.DateTimeField(null=True, blank=True)
    consent_recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recorded_communication_consents",
    )
    send_to_guardian = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["patient_id"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "patient"], name="comm_preference_patient_uniq")
        ]
        indexes = [models.Index(fields=["owner", "patient"], name="comm_pref_owner_patient_idx")]
