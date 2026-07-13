from __future__ import annotations

from django.conf import settings
from django.db import models

from .communication import Communication


class CommunicationChannelConfig(models.Model):
    class ConnectionStatus(models.TextChoices):
        NOT_CONFIGURED = "not_configured", "Não configurado"
        CONFIGURED = "configured", "Configurado"
        ERROR = "error", "Com erro"
        DISABLED = "disabled", "Desativado"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="communication_channel_configs",
    )
    channel = models.CharField(max_length=24, choices=Communication.Channel.choices)
    provider = models.CharField(max_length=60, blank=True)
    is_active = models.BooleanField(default=False)
    sender = models.CharField(max_length=160, blank=True)
    public_identifier = models.CharField(max_length=160, blank=True)
    connection_status = models.CharField(
        max_length=24,
        choices=ConnectionStatus.choices,
        default=ConnectionStatus.NOT_CONFIGURED,
    )
    last_validated_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["owner", "channel"], name="comm_channel_owner_uniq")
        ]
