"""Modelos de convite de cadastro de pacientes."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from .patient import Patient


class PatientRegistrationInvite(models.Model):
    """Convite temporário para o paciente complementar seu cadastro."""

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="registration_invites",
    )
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="patient_registration_invites_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["expires_at", "used_at"], name="patient_invite_validity_idx")]

    @property
    def is_valid(self) -> bool:
        return self.used_at is None and self.expires_at > timezone.now()
