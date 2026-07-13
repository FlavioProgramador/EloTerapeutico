from __future__ import annotations

from django.db import models

from apps.core.fields import EncryptedTextField

from .communication import Communication


class CommunicationRecipient(models.Model):
    class RecipientType(models.TextChoices):
        PATIENT = "patient", "Paciente"
        GUARDIAN = "guardian", "Responsável legal"
        PROFESSIONAL = "professional", "Profissional"
        USER = "user", "Usuário"
        CUSTOM = "custom", "Personalizado"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        READY = "ready", "Pronto"
        BLOCKED = "blocked", "Bloqueado"
        SENT = "sent", "Enviado"
        FAILED = "failed", "Falhou"

    communication = models.ForeignKey(Communication, on_delete=models.CASCADE, related_name="recipients")
    patient = models.ForeignKey(
        "patients.Patient",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="communication_recipients",
    )
    recipient_type = models.CharField(max_length=20, choices=RecipientType.choices)
    name = models.CharField(max_length=255)
    destination = EncryptedTextField()
    destination_masked = models.CharField(max_length=255)
    channel = models.CharField(max_length=24, choices=Communication.Channel.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    blocked_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        indexes = [models.Index(fields=["communication", "status"], name="comm_recipient_status_idx")]

    def __str__(self) -> str:
        return f"Destinatário #{self.pk} de comunicação #{self.communication_id}"


class CommunicationAttempt(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PROCESSING = "processing", "Processando"
        SUCCESS = "success", "Sucesso"
        RETRYABLE_FAILURE = "retryable_failure", "Falha temporária"
        PERMANENT_FAILURE = "permanent_failure", "Falha permanente"

    communication = models.ForeignKey(Communication, on_delete=models.CASCADE, related_name="attempts")
    recipient = models.ForeignKey(CommunicationRecipient, on_delete=models.CASCADE, related_name="attempts")
    attempt_number = models.PositiveSmallIntegerField()
    provider = models.CharField(max_length=60)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    external_id = models.CharField(max_length=160, blank=True)
    response_code = models.CharField(max_length=40, blank=True)
    error_code = models.CharField(max_length=80, blank=True)
    error_message = models.CharField(max_length=500, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True, db_index=True)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["communication", "recipient", "attempt_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["communication", "recipient", "attempt_number"],
                name="comm_attempt_number_uniq",
            )
        ]
        indexes = [models.Index(fields=["status", "next_retry_at"], name="comm_attempt_retry_idx")]
