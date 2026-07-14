from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.fields import EncryptedTextField

from .communication import Communication


class InAppNotification(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Baixa"
        NORMAL = "normal", "Normal"
        HIGH = "high", "Alta"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_notifications",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="in_app_notifications",
    )
    communication = models.ForeignKey(
        Communication,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
    )
    title = models.CharField(max_length=160)
    message = models.CharField(max_length=500)
    notification_type = models.CharField(max_length=80, db_index=True)
    priority = models.CharField(max_length=12, choices=Priority.choices, default=Priority.NORMAL)
    internal_url = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read", "created_at"], name="comm_notification_unread_idx")]


class InboundMessage(models.Model):
    class Status(models.TextChoices):
        UNMATCHED = "unmatched", "Não identificada"
        RECEIVED = "received", "Recebida"
        REVIEWED = "reviewed", "Revisada"
        LINKED = "linked", "Relacionada"
        ARCHIVED = "archived", "Arquivada"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inbound_messages")
    patient = models.ForeignKey(
        "patients.Patient",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inbound_messages",
    )
    sender_masked = models.CharField(max_length=255)
    channel = models.CharField(max_length=24, choices=Communication.Channel.choices)
    provider = models.CharField(max_length=60)
    external_id = models.CharField(max_length=160)
    body = EncryptedTextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED)
    communication = models.ForeignKey(
        Communication,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inbound_messages",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_inbound_messages",
    )
    received_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "external_id"], name="comm_inbound_external_uniq")
        ]
