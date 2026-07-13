from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from .communication import Communication


class PublicCommunicationActionToken(models.Model):
    class Purpose(models.TextChoices):
        CONFIRM_APPOINTMENT = "confirm_appointment", "Confirmar consulta"
        CANCEL_REQUEST = "cancel_request", "Solicitar cancelamento"
        RESCHEDULE_REQUEST = "reschedule_request", "Solicitar reagendamento"
        FORM_ACCESS = "form_access", "Acessar formulário"
        DOCUMENT_ACCESS = "document_access", "Acessar documento"
        ACKNOWLEDGE = "acknowledge", "Confirmar recebimento"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="communication_tokens")
    patient = models.ForeignKey(
        "patients.Patient",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="communication_tokens",
    )
    communication = models.ForeignKey(
        Communication,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="public_tokens",
    )
    appointment = models.ForeignKey(
        "agenda.Appointment",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="communication_tokens",
    )
    form_submission = models.ForeignKey(
        "forms.FormSubmission",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="communication_tokens",
    )
    document = models.ForeignKey(
        "documents.GeneratedDocument",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="communication_tokens",
    )
    purpose = models.CharField(max_length=32, choices=Purpose.choices)
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["purpose", "expires_at"], name="comm_token_expiry_idx")]

    @classmethod
    def issue(
        cls,
        *,
        owner,
        purpose,
        patient=None,
        communication=None,
        appointment=None,
        form_submission=None,
        document=None,
        ttl_hours=48,
        metadata=None,
    ):
        raw_token = secrets.token_urlsafe(32)
        instance = cls.objects.create(
            owner=owner,
            patient=patient,
            communication=communication,
            appointment=appointment,
            form_submission=form_submission,
            document=document,
            purpose=purpose,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=timezone.now() + timedelta(hours=ttl_hours),
            metadata=metadata or {},
        )
        return instance, raw_token

    @classmethod
    def resolve(cls, raw_token: str):
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        return cls.objects.select_related(
            "owner", "patient", "communication", "appointment", "form_submission__form", "document"
        ).filter(
            token_hash=token_hash,
            used_at__isnull=True,
            revoked_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).first()
