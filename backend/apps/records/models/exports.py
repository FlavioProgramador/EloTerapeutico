"""Fila de exportações clínicas."""

from django.conf import settings
from django.db import models

from .paths import clinical_export_path


class ClinicalExport(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendente"
        PROCESSING = "PROCESSING", "Processando"
        COMPLETED = "COMPLETED", "Concluído"
        FAILED = "FAILED", "Falhou"
        EXPIRED = "EXPIRED", "Expirado"

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="clinical_exports",
        verbose_name="Paciente",
    )
    export_type = models.CharField(max_length=100, verbose_name="Tipo de exportação")
    filename = models.CharField(max_length=255, verbose_name="Nome do arquivo")
    file = models.FileField(
        upload_to=clinical_export_path,
        null=True,
        blank=True,
        verbose_name="Arquivo gerado",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="clinical_exports_created",
        verbose_name="Criado por",
    )
    period = models.CharField(max_length=100, blank=True, verbose_name="Período")
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Status",
    )
    size_bytes = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Tamanho (bytes)",
    )
    download_url = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="URL de download",
    )
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Iniciado em")
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Finalizado em",
    )
    next_attempt_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Próxima tentativa em",
    )
    worker_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ID do Worker",
    )
    retries = models.IntegerField(default=0, verbose_name="Tentativas")
    error_message = models.TextField(blank=True, verbose_name="Mensagem de erro")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Exportação Clínica"
        verbose_name_plural = "Exportações Clínicas"
        indexes = [
            models.Index(
                fields=["patient", "status"],
                name="export_patient_status_idx",
            )
        ]
