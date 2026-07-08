"""Modelos de vínculo profissional de pacientes."""

from django.conf import settings
from django.db import models

from .patient import Patient


class PatientProfessional(models.Model):
    """Profissionais adicionais autorizados a acompanhar o paciente."""

    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name="professional_links",
    )
    professional = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="patient_professional_links",
        limit_choices_to={"role": "therapist"},
    )
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="patient_professionals_assigned",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "professional__full_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "professional"],
                name="unique_patient_professional",
            )
        ]
        indexes = [
            models.Index(
                fields=["professional", "is_active"],
                name="pat_prof_active_idx",
            )
        ]
