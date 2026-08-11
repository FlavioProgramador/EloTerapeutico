from __future__ import annotations

from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.fields.encrypted import EncryptedTextField


def generate_provider_room_name() -> str:
    """Gera um identificador opaco sem dados pessoais ou IDs sequenciais."""

    return f"tm_{uuid4().hex}"


class TelemedicineRoom(models.Model):
    """Sala técnica de uma consulta remota, isolada por organização."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        AVAILABLE = "available", "Disponível"
        WAITING = "waiting", "Aguardando participante"
        IN_PROGRESS = "in_progress", "Em andamento"
        FINISHED = "finished", "Finalizada"
        CANCELLED = "cancelled", "Cancelada"
        EXPIRED = "expired", "Expirada"
        FAILED = "failed", "Falhou"

    TERMINAL_STATUSES = {
        Status.FINISHED,
        Status.CANCELLED,
        Status.EXPIRED,
        Status.FAILED,
    }
    ALLOWED_TRANSITIONS = {
        Status.PENDING: {Status.AVAILABLE, Status.CANCELLED, Status.EXPIRED, Status.FAILED},
        Status.AVAILABLE: {Status.WAITING, Status.IN_PROGRESS, Status.CANCELLED, Status.EXPIRED, Status.FAILED},
        Status.WAITING: {Status.IN_PROGRESS, Status.FINISHED, Status.CANCELLED, Status.EXPIRED, Status.FAILED},
        Status.IN_PROGRESS: {Status.WAITING, Status.FINISHED, Status.CANCELLED, Status.FAILED},
        Status.FINISHED: set(),
        Status.CANCELLED: set(),
        Status.EXPIRED: set(),
        Status.FAILED: set(),
    }

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="telemedicine_rooms",
    )
    appointment = models.OneToOneField(
        "agenda.Appointment",
        on_delete=models.CASCADE,
        related_name="telemedicine_room",
    )
    public_id = models.UUIDField(default=uuid4, unique=True, editable=False)
    provider = models.CharField(max_length=32, default="livekit")
    provider_room_name = models.CharField(
        max_length=80,
        default=generate_provider_room_name,
        unique=True,
        editable=False,
    )
    provider_room_sid = models.CharField(max_length=128, blank=True)
    e2ee_key = EncryptedTextField(blank=True, default="")
    e2ee_enabled = models.BooleanField(default=True)

    # Compatibilidade temporária. Novos acessos usam TelemedicineInvitation.
    patient_token = models.UUIDField(null=True, blank=True, unique=True, editable=False)
    professional_token = models.UUIDField(null=True, blank=True, unique=True, editable=False)

    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    patient_joined_at = models.DateTimeField(null=True, blank=True)
    professional_joined_at = models.DateTimeField(null=True, blank=True)
    last_participant_left_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="closed_telemedicine_rooms",
    )
    failure_code = models.CharField(max_length=64, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["appointment__start_time"]
        indexes = [
            models.Index(fields=["organization", "status"], name="telemed_org_status_idx"),
            models.Index(fields=["organization", "expires_at"], name="telemed_org_expiry_idx"),
        ]

    def clean(self):
        super().clean()
        if self.appointment_id and self.appointment.organization_id != self.organization_id:
            raise ValidationError({"appointment": "A consulta pertence a outra organização."})

    @property
    def is_accessible(self) -> bool:
        return bool(
            not self.revoked_at
            and self.expires_at > timezone.now()
            and self.status not in self.TERMINAL_STATUSES
        )

    def transition_to(self, new_status: str, *, save: bool = True) -> None:
        if new_status == self.status:
            return
        current_status = self.Status(self.status)
        target_status = self.Status(new_status)
        allowed = self.ALLOWED_TRANSITIONS.get(current_status, set())
        if target_status not in allowed:
            raise ValidationError(
                {"status": f"Transição inválida de {self.status} para {new_status}."}
            )
        self.status = target_status
        if target_status == self.Status.IN_PROGRESS and not self.started_at:
            self.started_at = timezone.now()
        if target_status in self.TERMINAL_STATUSES and not self.ended_at:
            self.ended_at = timezone.now()
        if save:
            self.save()

    def revoke(self, *, actor=None, status: str | None = None) -> None:
        target_status = status or self.Status.CANCELLED
        if self.status not in self.TERMINAL_STATUSES:
            self.transition_to(target_status, save=False)
        self.revoked_at = timezone.now()
        self.closed_by = actor
        self.save()
        self.invitations.filter(revoked_at__isnull=True).update(
            revoked_at=timezone.now(),
            updated_at=timezone.now(),
        )


class TelemedicineInvitation(models.Model):
    """Convite público persistido somente como hash criptográfico."""

    class Role(models.TextChoices):
        PATIENT = "patient", "Paciente"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="telemedicine_invitations",
    )
    room = models.ForeignKey(
        TelemedicineRoom,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PATIENT)
    token_hash = models.CharField(max_length=64, unique=True, editable=False)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_telemedicine_invitations",
    )
    last_used_at = models.DateTimeField(null=True, blank=True)
    use_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["room", "role"],
                condition=Q(revoked_at__isnull=True),
                name="uniq_active_telemed_invite",
            )
        ]
        indexes = [
            models.Index(
                fields=["organization", "expires_at"],
                name="telemed_inv_org_exp_idx",
            )
        ]

    @property
    def is_valid(self) -> bool:
        return bool(
            not self.revoked_at
            and self.expires_at > timezone.now()
            and self.room.is_accessible
        )

    def clean(self):
        super().clean()
        if self.room_id and self.room.organization_id != self.organization_id:
            raise ValidationError({"room": "A sala pertence a outra organização."})


class TelemedicineConsent(models.Model):
    """Evidência versionada do consentimento para a consulta remota."""

    class AcceptanceMethod(models.TextChoices):
        PATIENT_LINK = "patient_link", "Link do paciente"
        RESPONSIBLE_LINK = "responsible_link", "Link do responsável"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="telemedicine_consents",
    )
    room = models.ForeignKey(
        TelemedicineRoom,
        on_delete=models.CASCADE,
        related_name="consents",
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="telemedicine_consents",
    )
    responsible_guardian_name = models.CharField(max_length=180, blank=True)
    document_version = models.CharField(max_length=32)
    document_hash = models.CharField(max_length=64)
    accepted_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)
    acceptance_method = models.CharField(
        max_length=32,
        choices=AcceptanceMethod.choices,
        default=AcceptanceMethod.PATIENT_LINK,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-accepted_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["room"],
                condition=Q(revoked_at__isnull=True),
                name="uniq_active_telemed_consent",
            )
        ]

    def clean(self):
        super().clean()
        if self.room_id and self.room.organization_id != self.organization_id:
            raise ValidationError({"room": "A sala pertence a outra organização."})
        if self.room_id and self.patient_id != self.room.appointment.patient_id:
            raise ValidationError({"patient": "O paciente não pertence à consulta."})


class TelemedicineParticipantSession(models.Model):
    """Metadados operacionais de entrada e saída, sem conteúdo da chamada."""

    class Role(models.TextChoices):
        PATIENT = "patient", "Paciente"
        PROFESSIONAL = "professional", "Profissional"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="telemedicine_participant_sessions",
    )
    room = models.ForeignKey(
        TelemedicineRoom,
        on_delete=models.CASCADE,
        related_name="participant_sessions",
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    provider_participant_identity = models.CharField(max_length=180)
    provider_participant_sid = models.CharField(max_length=128, blank=True)
    joined_at = models.DateTimeField(default=timezone.now)
    left_at = models.DateTimeField(null=True, blank=True)
    disconnect_reason = models.CharField(max_length=64, blank=True)
    connection_aborted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-joined_at"]
        indexes = [
            models.Index(
                fields=["organization", "room", "role"],
                name="telemed_part_org_room_idx",
            )
        ]


class TelemedicineWebhookEvent(models.Model):
    """Registro mínimo para idempotência de eventos do provedor."""

    provider = models.CharField(max_length=32, default="livekit")
    provider_event_id = models.CharField(max_length=180)
    event_type = models.CharField(max_length=64)
    occurred_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    room = models.ForeignKey(
        TelemedicineRoom,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="webhook_events",
    )
    payload_hash = models.CharField(max_length=64)
    processing_error = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-received_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_event_id"],
                name="uniq_telemed_provider_event",
            )
        ]
        indexes = [
            models.Index(
                fields=["provider", "event_type", "received_at"],
                name="telemed_event_type_idx",
            )
        ]


class AppointmentReminder(models.Model):
    """Lembrete administrativo sem conteúdo clínico e com tenant explícito."""

    class Channel(models.TextChoices):
        WHATSAPP = "whatsapp", "WhatsApp"
        EMAIL = "email", "E-mail"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        SENT = "sent", "Enviado"
        FAILED = "failed", "Falhou"
        CANCELLED = "cancelled", "Cancelado"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="appointment_reminders",
    )
    appointment = models.ForeignKey(
        "agenda.Appointment",
        on_delete=models.CASCADE,
        related_name="reminders",
    )
    channel = models.CharField(
        max_length=20,
        choices=Channel.choices,
        default=Channel.WHATSAPP,
    )
    scheduled_for = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    recipient_masked = models.CharField(max_length=32, blank=True)
    error_message = models.CharField(max_length=255, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_for"]
        indexes = [
            models.Index(
                fields=["organization", "status", "scheduled_for"],
                name="reminder_org_status_idx",
            ),
            models.Index(
                fields=["status", "scheduled_for"],
                name="reminder_status_time_idx",
            ),
        ]

    def clean(self):
        super().clean()
        if self.appointment_id and self.appointment.organization_id != self.organization_id:
            raise ValidationError({"appointment": "A consulta pertence a outra organização."})
