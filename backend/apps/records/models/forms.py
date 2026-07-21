"""Respostas de formulários clínicos vinculadas ao prontuário."""

from django.conf import settings
from django.db import models

from .tenant import ClinicalTenantModel


class ClinicalFormResponse(ClinicalTenantModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        COMPLETED = "completed", "Concluído"

    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE, related_name="form_responses", verbose_name="Paciente")
    form_name = models.CharField(max_length=255, verbose_name="Nome do formulário")
    category = models.CharField(max_length=100, verbose_name="Categoria")
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Enviado em")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Preenchido em")
    completed_by = models.CharField(max_length=255, blank=True, verbose_name="Preenchido por")
    therapist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="form_responses", verbose_name="Profissional responsável")
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.COMPLETED, verbose_name="Status")
    answers_count = models.IntegerField(default=0, verbose_name="Quantidade de respostas")
    form_snapshot = models.JSONField(default=dict, blank=True, verbose_name="Snapshot do formulário")
    answers = models.JSONField(default=dict, blank=True, verbose_name="Respostas")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        ordering = ["-completed_at", "-created_at"]
        verbose_name = "Resposta de Formulário"
        verbose_name_plural = "Respostas de Formulários"
        indexes = [
            models.Index(fields=["organization", "patient", "status"], name="form_resp_org_patient_idx"),
            models.Index(fields=["patient", "status"], name="form_resp_patient_status_idx"),
        ]
