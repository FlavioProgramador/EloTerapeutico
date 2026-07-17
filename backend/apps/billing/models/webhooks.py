from __future__ import annotations

from django.db import models
from django.db.models import Q


class WebhookEvent(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "RECEIVED", "Recebido"
        PROCESSING = "PROCESSING", "Processando"
        PROCESSED = "PROCESSED", "Processado"
        RETRY = "RETRY", "Aguardando nova tentativa"
        FAILED = "FAILED", "Falhou"
        IGNORED = "IGNORED", "Ignorado"

    gateway_name = models.CharField(max_length=40)
    event_id = models.CharField(max_length=160, unique=True, null=True, blank=True)
    event_type = models.CharField(max_length=120)
    payload_hash = models.CharField(max_length=64, unique=True)
    payload = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED,
        db_index=True,
    )
    attempt_count = models.PositiveIntegerField(default=0)
    next_retry_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    # Compatibilidade temporária com o contrato anterior.
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-received_at"]
        verbose_name = "Evento de webhook"
        verbose_name_plural = "Eventos de webhook"
        indexes = [
            models.Index(
                fields=["gateway_name", "event_type"],
                name="billing_webhook_type_idx",
            ),
            models.Index(
                fields=["status", "next_retry_at"],
                name="billing_webhook_retry_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(processed=False, processed_at__isnull=True)
                    | Q(processed=True, processed_at__isnull=False)
                ),
                name="billing_webhook_processed_timestamp_consistent",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.gateway_name} — {self.event_type}"
