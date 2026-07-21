from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.fields import EncryptedTextField

from .communication import Communication


class InAppNotification(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Baixa"
        NORMAL = "normal", "Normal"
        HIGH = "high", "Alta"
        CRITICAL = "critical", "Crítica"

    class Category(models.TextChoices):
        AGENDA = "agenda", "Agenda"
        PATIENTS = "patients", "Pacientes"
        RECORDS = "records", "Prontuário"
        DOCUMENTS = "documents", "Documentos"
        FINANCIAL = "financial", "Financeiro"
        BILLING = "billing", "Assinatura"
        COMMUNICATIONS = "communications", "Comunicação interna"
        FORMS = "forms", "Formulários"
        SECURITY = "security", "Segurança"
        SYSTEM = "system", "Sistema"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="in_app_notifications",
        db_index=True,
    )
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
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="triggered_notifications",
    )
    communication = models.ForeignKey(
        Communication,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
    )
    category = models.CharField(
        max_length=24,
        choices=Category.choices,
        default=Category.SYSTEM,
        db_index=True,
    )
    title = models.CharField(max_length=160)
    message = models.CharField(max_length=500)
    notification_type = models.CharField(max_length=80, db_index=True)
    priority = models.CharField(
        max_length=12,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )
    internal_url = models.CharField(max_length=500, blank=True)
    action_label = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["organization", "recipient", "is_read", "created_at"],
                name="comm_notif_org_unread_idx",
            ),
            models.Index(
                fields=["recipient", "is_read", "created_at"],
                name="comm_notification_unread_idx",
            ),
            models.Index(
                fields=["recipient", "archived_at", "created_at"],
                name="comm_notif_archive_idx",
            ),
            models.Index(
                fields=["recipient", "category", "created_at"],
                name="comm_notif_category_idx",
            ),
        ]

    def clean(self):
        super().clean()
        communication = self.communication if self.communication_id else None
        if communication is not None and communication.organization_id != self.organization_id:
            raise ValidationError({"communication": "A comunicação pertence a outra organização."})


class NotificationPreference(models.Model):
    """Preferência pessoal global do usuário para notificações do produto."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    in_app_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=False)
    whatsapp_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=False)
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=64, default="America/Sao_Paulo")
    category_preferences = models.JSONField(default=dict, blank=True)
    daily_digest_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Preferências de notificações de {self.user.email}"


class NotificationDelivery(models.Model):
    class Channel(models.TextChoices):
        IN_APP = "in_app", "No sistema"
        EMAIL = "email", "E-mail"
        WHATSAPP = "whatsapp", "WhatsApp"
        PUSH = "push", "Push"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PROCESSING = "processing", "Processando"
        SENT = "sent", "Enviado"
        DELIVERED = "delivered", "Entregue"
        FAILED = "failed", "Falhou"
        SKIPPED = "skipped", "Ignorado"

    notification = models.ForeignKey(
        InAppNotification,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    channel = models.CharField(max_length=20, choices=Channel.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    attempt_count = models.PositiveSmallIntegerField(default=0)
    provider = models.CharField(max_length=80, blank=True)
    provider_reference = models.CharField(max_length=160, blank=True)
    scheduled_at = models.DateTimeField(default=timezone.now, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_error = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["notification_id", "channel"]
        constraints = [
            models.UniqueConstraint(
                fields=["notification", "channel"],
                name="comm_notif_delivery_channel_uniq",
            )
        ]
        indexes = [
            models.Index(
                fields=["status", "next_retry_at"],
                name="comm_notif_delivery_retry_idx",
            )
        ]


class InboundMessage(models.Model):
    class Status(models.TextChoices):
        UNMATCHED = "unmatched", "Não identificada"
        RECEIVED = "received", "Recebida"
        REVIEWED = "reviewed", "Revisada"
        LINKED = "linked", "Relacionada"
        ARCHIVED = "archived", "Arquivada"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="inbound_messages",
        db_index=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inbound_messages",
    )
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
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RECEIVED,
    )
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
            models.UniqueConstraint(
                fields=["organization", "provider", "external_id"],
                name="comm_inbound_org_external_uniq",
            )
        ]
        indexes = [
            models.Index(
                fields=["organization", "status", "received_at"],
                name="comm_inbound_org_status_idx",
            )
        ]

    def clean(self):
        super().clean()
        patient = self.patient if self.patient_id else None
        if patient is not None and patient.organization_id != self.organization_id:
            raise ValidationError({"patient": "O paciente pertence a outra organização."})

        communication = self.communication if self.communication_id else None
        if communication is not None and communication.organization_id != self.organization_id:
            raise ValidationError({"communication": "A comunicação pertence a outra organização."})
