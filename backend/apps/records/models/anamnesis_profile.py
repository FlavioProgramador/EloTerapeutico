"""Perfil ampliado de anamnese."""

from django.conf import settings
from django.db import models

from apps.core.fields import EncryptedTextField


class AnamnesisProfile(models.Model):
    anamnesis = models.OneToOneField(
        "records.Anamnesis",
        on_delete=models.PROTECT,
        related_name="profile",
    )
    reason_for_care = EncryptedTextField(blank=True, default="")
    physical_health_history = EncryptedTextField(blank=True, default="")
    mental_health_history = EncryptedTextField(blank=True, default="")
    previous_treatments = EncryptedTextField(blank=True, default="")
    habits_and_routine = EncryptedTextField(blank=True, default="")
    sleep = EncryptedTextField(blank=True, default="")
    nutrition = EncryptedTextField(blank=True, default="")
    family_social_relations = EncryptedTextField(blank=True, default="")
    academic_history = EncryptedTextField(blank=True, default="")
    professional_history = EncryptedTextField(blank=True, default="")
    support_network = EncryptedTextField(blank=True, default="")
    relevant_events = EncryptedTextField(blank=True, default="")
    initial_assessment = EncryptedTextField(blank=True, default="")
    clinical_hypotheses = EncryptedTextField(blank=True, default="")
    custom_fields = EncryptedTextField(blank=True, default="{}")
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="anamnesis_profiles_updated",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil ampliado de anamnese"
        verbose_name_plural = "Perfis ampliados de anamnese"
