from __future__ import annotations

import json
from typing import Any

from django.conf import settings
from django.db import models

from apps.core.fields import EncryptedTextField

from .communication import Communication


class CommunicationChannelConfig(models.Model):
    class ConnectionStatus(models.TextChoices):
        NOT_CONFIGURED = "not_configured", "Não configurado"
        INCOMPLETE = "incomplete", "Configuração incompleta"
        VALIDATING = "validating", "Validando"
        CONFIGURED = "configured", "Configurado"
        ERROR = "error", "Com erro"
        DISABLED = "disabled", "Desativado"
        UNAVAILABLE = "unavailable", "Indisponível temporariamente"

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
    metadata = models.JSONField(default=dict, blank=True)
    credentials = EncryptedTextField(default="", blank=True)
    last_validated_at = models.DateTimeField(null=True, blank=True)
    last_tested_at = models.DateTimeField(null=True, blank=True)
    last_error_code = models.CharField(max_length=80, blank=True)
    last_error_message = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["owner", "channel"], name="comm_channel_owner_uniq")
        ]
        indexes = [
            models.Index(
                fields=["owner", "is_active", "connection_status"],
                name="comm_channel_oper_idx",
            )
        ]

    def get_credentials(self) -> dict[str, Any]:
        if not self.credentials:
            return {}
        try:
            payload = json.loads(self.credentials)
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def set_credentials(self, payload: dict[str, Any] | None) -> None:
        self.credentials = json.dumps(payload or {}, ensure_ascii=False, sort_keys=True)

    def clear_validation_error(self) -> None:
        self.last_error_code = ""
        self.last_error_message = ""
