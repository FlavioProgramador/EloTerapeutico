"""
apps/agenda/models.py
Modelos de agendamento de consultas para o Elo Terapêutico.

Inclui:
  - Appointment: representa uma consulta agendada entre terapeuta e paciente.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class Appointment(models.Model):
    """
    Representa uma consulta/sessão agendada.

    Suporta consultas avulsas e recorrentes (semanal, quinzenal, mensal).
    Cada ocorrência recorrente é uma linha independente nesta tabela,
    ligada à consulta-pai por meio do campo `parent_appointment`.
    """

    # ─────────────────────────────────────────────────────────────────────────
    # Opções de status da consulta
    # ─────────────────────────────────────────────────────────────────────────
    class Status(models.TextChoices):
        SCHEDULED   = "scheduled",   "Agendada"
        CONFIRMED   = "confirmed",   "Confirmada"
        MISSED      = "missed",      "Faltou"
        CANCELLED   = "cancelled",   "Cancelada"
        RESCHEDULED = "rescheduled", "Reagendada"

    # Regras de recorrência suportadas
    class RecurrenceRule(models.TextChoices):
        WEEKLY    = "WEEKLY",    "Semanal"
        BIWEEKLY  = "BIWEEKLY", "Quinzenal"
        MONTHLY   = "MONTHLY",  "Mensal"

    # ─────────────────────────────────────────────────────────────────────────
    # Relações principais
    # ─────────────────────────────────────────────────────────────────────────
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Paciente",
    )
    therapist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name="Terapeuta",
        limit_choices_to={"role": "therapist"},
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Dados da consulta
    # ─────────────────────────────────────────────────────────────────────────
    start_time = models.DateTimeField(verbose_name="Início")
    end_time   = models.DateTimeField(verbose_name="Término")
    duration_minutes = models.PositiveIntegerField(
        default=50,
        verbose_name="Duração (min)",
        help_text="Preenchido automaticamente a partir do horário de início/fim.",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        verbose_name="Status",
        db_index=True,
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

    session_value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Valor da sessão (R$)",
        help_text="Valor cobrado nesta consulta específica.",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Recorrência
    # ─────────────────────────────────────────────────────────────────────────
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
    parent_appointment = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recurrences",
        verbose_name="Consulta-pai (série recorrente)",
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Auditoria
    # ─────────────────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Consulta"
        verbose_name_plural = "Consultas"
        ordering = ["-start_time"]
        indexes = [
            # Busca de agenda por terapeuta em um período
            models.Index(
                fields=["therapist", "start_time"],
                name="idx_appt_therapist_start",
            ),
            # Busca do histórico de consultas por paciente
            models.Index(
                fields=["patient", "start_time"],
                name="idx_appt_patient_start",
            ),
            # Filtro rápido por status
            models.Index(fields=["status"], name="idx_appt_status"),
        ]

    def __str__(self):
        return (
            f"{self.patient} com {self.therapist.full_name} "
            f"em {self.start_time.strftime('%d/%m/%Y %H:%M')} [{self.get_status_display()}]"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Propriedades
    # ─────────────────────────────────────────────────────────────────────────
    @property
    def duration_display(self) -> str:
        """Retorna a duração formatada como string legível. Ex: '50 min'."""
        return f"{self.duration_minutes} min"

    # ─────────────────────────────────────────────────────────────────────────
    # Método de negócio: verificação de conflito de horário
    # ─────────────────────────────────────────────────────────────────────────
    @classmethod
    def check_conflict(
        cls,
        therapist,
        start_time,
        end_time,
        exclude_id=None,
    ) -> bool:
        """
        Verifica se existe consulta conflitante para o terapeuta no intervalo
        [start_time, end_time].

        Retorna True se houver conflito, False caso contrário.

        Um conflito ocorre quando os intervalos se sobrepõem, ou seja:
            existing.start_time < end_time AND existing.end_time > start_time

        Parâmetros:
            therapist  : instância de User (terapeuta)
            start_time : datetime de início da nova consulta
            end_time   : datetime de fim da nova consulta
            exclude_id : ID da própria consulta a ignorar (em caso de update)
        """
        qs = cls.objects.filter(
            therapist=therapist,
            # Interseção de intervalos: novo início antes do fim existente
            # e novo fim depois do início existente.
            start_time__lt=end_time,
            end_time__gt=start_time,
            # Só verifica consultas "ativas" (não canceladas/remarcadas)
            status__in=[cls.Status.SCHEDULED, cls.Status.CONFIRMED],
        )
        if exclude_id is not None:
            qs = qs.exclude(pk=exclude_id)
        return qs.exists()

    # ─────────────────────────────────────────────────────────────────────────
    # Override save: calcula duration_minutes automaticamente
    # ─────────────────────────────────────────────────────────────────────────
    def save(self, *args, **kwargs):
        """Calcula a duração em minutos antes de salvar."""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() // 60)
        super().save(*args, **kwargs)
