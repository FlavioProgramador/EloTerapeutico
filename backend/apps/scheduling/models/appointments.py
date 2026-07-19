# mypy: ignore-errors
from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from .packages import PatientPackage
from .rooms import AppointmentRecurrence, Room

ACTIVE_APPOINTMENT_STATUSES = ("scheduled", "confirmed")


class Appointment(models.Model):
    """Consulta ou sessão agendada entre profissional e paciente."""

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Agendada"
        CONFIRMED = "confirmed", "Confirmada"
        COMPLETED = "completed", "Realizada"
        MISSED = "missed", "Faltou"
        CANCELLED = "cancelled", "Cancelada"
        RESCHEDULED = "rescheduled", "Reagendada"

    class Modality(models.TextChoices):
        IN_PERSON = "in_person", "Presencial"
        ONLINE = "online", "Online"
        HYBRID = "hybrid", "Híbrida"

    class AppointmentType(models.TextChoices):
        ASSESSMENT = "assessment", "Avaliação"
        PSYCHOTHERAPY = "psychotherapy", "Psicoterapia"
        FOLLOW_UP = "follow_up", "Retorno"
        GUIDANCE = "guidance", "Orientação"
        GROUP = "group", "Sessão em grupo"
        OTHER = "other", "Outro"

    class Origin(models.TextChoices):
        MANUAL = "manual", "Manual"
        RECURRENCE = "recurrence", "Recorrência"
        PACKAGE = "package", "Pacote"
        RESCHEDULE = "reschedule", "Remarcação"

    class RecurrenceRule(models.TextChoices):
        WEEKLY = "WEEKLY", "Semanal"
        BIWEEKLY = "BIWEEKLY", "Quinzenal"
        MONTHLY = "MONTHLY", "Mensal"

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Paciente",
    )
    participants = models.ManyToManyField(
        "patients.Patient",
        blank=True,
        related_name="group_appointments",
    )
    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="appointments",
        limit_choices_to={"role": "therapist"},
        verbose_name="Terapeuta",
    )
    start_time = models.DateTimeField(verbose_name="Início")
    end_time = models.DateTimeField(verbose_name="Término")
    duration_minutes = models.PositiveIntegerField(
        default=50,
        verbose_name="Duração (min)",
        help_text="Preenchido automaticamente a partir do horário de início/fim.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        db_index=True,
    )
    modality = models.CharField(
        max_length=20,
        choices=Modality.choices,
        default=Modality.IN_PERSON,
    )
    appointment_type = models.CharField(
        max_length=30,
        choices=AppointmentType.choices,
        default=AppointmentType.PSYCHOTHERAPY,
    )
    room = models.ForeignKey(
        Room,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments",
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Observações do agendamento",
        help_text="Observações visíveis para o terapeuta e secretária.",
    )
    cancellation_reason = models.TextField(
        blank=True,
        verbose_name="Motivo do cancelamento",
    )
    session_value = models.DecimalField(max_digits=10, decimal_places=2)
    origin = models.CharField(
        max_length=20,
        choices=Origin.choices,
        default=Origin.MANUAL,
    )
    is_recurring = models.BooleanField(
        default=False,
        verbose_name="Consulta recorrente",
    )
    recurrence_rule = models.CharField(
        max_length=20,
        blank=True,
        choices=RecurrenceRule.choices,
        verbose_name="Regra de recorrência",
        help_text="Ex: WEEKLY (semanal), BIWEEKLY (quinzenal), MONTHLY (mensal).",
    )
    recurrence = models.ForeignKey(
        AppointmentRecurrence,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments",
    )
    parent_appointment = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recurrences",
        verbose_name="Consulta-pai (série recorrente)",
    )
    package = models.ForeignKey(
        PatientPackage,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_appointments",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_appointments",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Consulta"
        verbose_name_plural = "Consultas"
        ordering = ["-start_time"]
        indexes = [
            models.Index(
                fields=["therapist", "start_time"],
                name="idx_appt_therapist_start",
            ),
            models.Index(
                fields=["patient", "start_time"],
                name="idx_appt_patient_start",
            ),
            models.Index(fields=["status"], name="idx_appt_status"),
            models.Index(fields=["room", "start_time"], name="appt_room_start_idx"),
            models.Index(
                fields=["recurrence", "start_time"],
                name="appt_rec_start_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=models.F("start_time")),
                name="appt_end_after_start",
            ),
            models.CheckConstraint(
                condition=Q(session_value__gte=0),
                name="appt_value_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"Consulta #{self.pk} em {self.start_time:%d/%m/%Y %H:%M}"

    @property
    def duration_display(self) -> str:
        return f"{self.duration_minutes} min"

    @classmethod
    def active_queryset(cls):
        return cls.objects.filter(status__in=ACTIVE_APPOINTMENT_STATUSES)

    @classmethod
    def conflict_details(
        cls,
        *,
        therapist,
        patient,
        start_time,
        end_time,
        room=None,
        participants=None,
        exclude_id=None,
    ) -> dict[str, bool]:
        """Compatibilidade: delega a consulta para o selector canônico."""

        from apps.scheduling.selectors.conflicts import get_appointment_conflicts

        return get_appointment_conflicts(
            therapist=therapist,
            patient=patient,
            start_time=start_time,
            end_time=end_time,
            room=room,
            participants=participants,
            exclude_appointment_id=exclude_id,
        ).as_dict()

    @classmethod
    def check_conflict(
        cls,
        therapist,
        start_time,
        end_time,
        exclude_id=None,
    ) -> bool:
        from apps.scheduling.selectors.conflicts import get_appointment_conflicts

        result = get_appointment_conflicts(
            therapist=therapist,
            patient=None,
            start_time=start_time,
            end_time=end_time,
            exclude_appointment_id=exclude_id,
        )
        return result.therapist

    def clean(self):
        super().clean()
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({"end_time": "O término deve ser posterior ao início."})
        if self.session_value is not None and self.session_value < 0:
            raise ValidationError({"session_value": "O valor não pode ser negativo."})
        if self.modality == self.Modality.ONLINE and self.room_id:
            raise ValidationError({"room": "Consultas online não utilizam sala física."})
        if self.room_id and not self.room.is_active:
            raise ValidationError({"room": "A sala selecionada está inativa."})

    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            self.duration_minutes = max(
                int((self.end_time - self.start_time).total_seconds() // 60),
                1,
            )
        super().save(*args, **kwargs)
