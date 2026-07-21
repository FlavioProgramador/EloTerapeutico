"""Modelo de anamnese base."""

from django.conf import settings
from django.db import models

from apps.core.fields import EncryptedTextField

from .tenant import ClinicalTenantModel


class Anamnesis(ClinicalTenantModel):
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="records_anamnesis_items",
        db_index=True,
    )
    patient = models.OneToOneField(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="anamnesis",
        verbose_name="Paciente",
    )
    chief_complaint = EncryptedTextField(verbose_name="Queixa principal")
    history = EncryptedTextField(blank=True, verbose_name="Histórico clínico")
    medications = EncryptedTextField(blank=True, verbose_name="Medicações em uso")
    family_history = EncryptedTextField(blank=True, verbose_name="Histórico familiar")
    observations = EncryptedTextField(blank=True, verbose_name="Observações gerais")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="anamneses_created",
        verbose_name="Criado por",
    )

    class Meta:
        verbose_name = "Anamnese"
        verbose_name_plural = "Anamneses"
        indexes = [
            models.Index(
                fields=["organization", "patient"],
                name="anamnesis_org_patient_idx",
            )
        ]

    def __str__(self):
        return f"Anamnese de {self.patient}"
