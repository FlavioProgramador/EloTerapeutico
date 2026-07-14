"""Modelo de anamnese base."""

from django.conf import settings
from django.db import models

from apps.core.fields import EncryptedTextField


class Anamnesis(models.Model):
    patient = models.OneToOneField(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="anamnesis",
        verbose_name="Paciente",
        help_text="Paciente ao qual esta anamnese pertence.",
    )
    chief_complaint = EncryptedTextField(
        verbose_name="Queixa principal",
        help_text="Motivo principal que levou o paciente a buscar terapia.",
    )
    history = EncryptedTextField(
        blank=True,
        verbose_name="Histórico clínico",
        help_text=("Histórico de tratamentos anteriores, diagnósticos e intercorrências."),
    )
    medications = EncryptedTextField(
        blank=True,
        verbose_name="Medicações em uso",
        help_text="Lista de medicamentos em uso no momento da avaliação inicial.",
    )
    family_history = EncryptedTextField(
        blank=True,
        verbose_name="Histórico familiar",
        help_text="Doenças e transtornos relevantes na família do paciente.",
    )
    observations = EncryptedTextField(
        blank=True,
        verbose_name="Observações gerais",
        help_text="Anotações adicionais não cobertas pelos campos anteriores.",
    )
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

    def __str__(self):
        return f"Anamnese de {self.patient}"
