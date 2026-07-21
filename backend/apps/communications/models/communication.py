from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.core.fields import EncryptedTextField


class Communication(models.Model):
    class Direction(models.TextChoices):
        OUTBOUND = "outbound", "Saída"
        INBOUND = "inbound", "Entrada"

    class Channel(models.TextChoices):
        IN_APP = "in_app", "Notificação interna"
        EMAIL = "email", "E-mail"
        WHATSAPP_MANUAL = "whatsapp_manual", "WhatsApp manual"
        WHATSAPP = "whatsapp", "WhatsApp Business"
        SMS = "sms", "SMS"

    class Category(models.TextChoices):
        APPOINTMENT_CONFIRMATION = "appointment_confirmation", "Confirmação de consulta"
        APPOINTMENT_REMINDER = "appointment_reminder", "Lembrete de consulta"
        APPOINTMENT_RESCHEDULED = "appointment_rescheduled", "Consulta reagendada"
        APPOINTMENT_CANCELED = "appointment_canceled", "Consulta cancelada"
        FORM_REQUEST = "form_request", "Solicitação de formulário"
        FORM_REMINDER = "form_reminder", "Lembrete de formulário"
        DOCUMENT_AVAILABLE = "document_available", "Documento disponível"
        DOCUMENT_SIGNATURE = "document_signature", "Assinatura de documento"
        PAYMENT_DUE = "payment_due", "Pagamento próximo do vencimento"
        PAYMENT_OVERDUE = "payment_overdue", "Pagamento vencido"
        PAYMENT_CONFIRMED = "payment_confirmed", "Pagamento confirmado"
        PACKAGE_ENDING = "package_ending", "Pacote próximo do fim"
        PATIENT_MESSAGE = "patient_message", "Mensagem ao paciente"
        SYSTEM_NOTIFICATION = "system_notification", "Notificação do sistema"
        OTHER = "other", "Outro"

    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        SCHEDULED = "scheduled", "Agendada"
        QUEUED = "queued", "Na fila"
        PROCESSING = "processing", "Processando"
        SENT = "sent", "Enviada"
        DELIVERED = "delivered", "Entregue"
        READ = "read", "Lida"
        RESPONDED = "responded", "Respondida"
        FAILED = "failed", "Falhou"
        CANCELED = "canceled", "Cancelada"
        EXPIRED = "expired", "Expirada"

    class Priority(models.TextChoices):
        LOW = "low", "Baixa"
        NORMAL = "normal", "Normal"
        HIGH = "high", "Alta"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="communications",
        db_index=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="communications",
        verbose_name="Proprietário",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_communications",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="communications",
    )
    appointment = models.ForeignKey(
        "agenda.Appointment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="communications",
    )
    form_submission = models.ForeignKey(
        "forms.FormSubmission",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="communications",
    )
    document = models.ForeignKey(
        "documents.GeneratedDocument",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="communications",
    )
    financial_transaction = models.ForeignKey(
        "financeiro.FinancialTransaction",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="communications",
    )
    direction = models.CharField(max_length=12, choices=Direction.choices, default=Direction.OUTBOUND)
    channel = models.CharField(max_length=24, choices=Channel.choices, db_index=True)
    category = models.CharField(max_length=40, choices=Category.choices, default=Category.OTHER, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    priority = models.CharField(max_length=12, choices=Priority.choices, default=Priority.NORMAL)
    subject = models.CharField(max_length=255, blank=True)
    body = EncryptedTextField(blank=True)
    body_html = EncryptedTextField(blank=True)
    structured_content = models.JSONField(default=dict, blank=True)
    template = models.ForeignKey(
        "CommunicationTemplate",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="communications",
    )
    template_snapshot = models.JSONField(default=dict, blank=True)
    variables_snapshot = models.JSONField(default=dict, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True, db_index=True)
    queued_at = models.DateTimeField(null=True, blank=True)
    next_retry_at = models.DateTimeField(null=True, blank=True, db_index=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=160)
    source_event = models.CharField(max_length=80, blank=True, db_index=True)
    source_object_type = models.CharField(max_length=80, blank=True)
    source_object_id = models.CharField(max_length=80, blank=True)
    provider_name = models.CharField(max_length=60, blank=True)
    provider_message_id = models.CharField(max_length=160, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Comunicação"
        verbose_name_plural = "Comunicações"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "idempotency_key"],
                name="comm_org_idempotency_uniq",
            ),
            models.CheckConstraint(
                condition=Q(scheduled_at__isnull=True)
                | Q(status__in=[
                    "scheduled",
                    "queued",
                    "processing",
                    "sent",
                    "delivered",
                    "read",
                    "responded",
                    "failed",
                    "canceled",
                    "expired",
                ]),
                name="comm_schedule_status_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["organization", "status"], name="comm_org_status_idx"),
            models.Index(fields=["organization", "channel"], name="comm_org_channel_idx"),
            models.Index(fields=["organization", "patient"], name="comm_org_patient_idx"),
            models.Index(fields=["owner", "status"], name="comm_owner_status_idx"),
            models.Index(fields=["owner", "channel"], name="comm_owner_channel_idx"),
            models.Index(fields=["owner", "patient"], name="comm_owner_patient_idx"),
            models.Index(fields=["scheduled_at", "status"], name="comm_due_queue_idx"),
        ]

    def clean(self):
        super().clean()
        for field_name in (
            "patient",
            "appointment",
            "form_submission",
            "document",
            "financial_transaction",
        ):
            relation_id = getattr(self, f"{field_name}_id", None)
            if relation_id:
                relation = getattr(self, field_name)
                if relation.organization_id != self.organization_id:
                    raise ValidationError(
                        {field_name: "O recurso pertence a outra organização."}
                    )
        if self.template_id and (
            not self.template.is_system_template
            and self.template.organization_id != self.organization_id
        ):
            raise ValidationError({"template": "O template pertence a outra organização."})

    def __str__(self) -> str:
        return f"Comunicação #{self.pk} ({self.channel}/{self.status})"

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            self.Status.DELIVERED,
            self.Status.READ,
            self.Status.RESPONDED,
            self.Status.CANCELED,
            self.Status.EXPIRED,
        }
