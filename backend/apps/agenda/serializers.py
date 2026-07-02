"""
apps/agenda/serializers.py
Serializers para o app de agenda de consultas.

Serializers disponíveis:
  - AppointmentListSerializer     : listagem resumida
  - AppointmentDetailSerializer   : detalhamento completo (nested read-only)
  - AppointmentCreateSerializer   : criação com validações de negócio
  - AppointmentUpdateSerializer   : atualização (suporta alteração parcial de campos)
  - AppointmentStatusUpdateSerializer: atualização restrita de status
  - CheckAvailabilitySerializer   : verifica slots livres em uma data
"""

import logging
from datetime import date, datetime, timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from apps.users.models import WorkingHours

from .models import Appointment

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Sub-serializers auxiliares (nested, somente leitura)
# ─────────────────────────────────────────────────────────────────────────────

class PatientSummarySerializer(serializers.Serializer):
    """Representação resumida do paciente para uso em nested read-only."""
    id        = serializers.IntegerField()
    full_name = serializers.CharField()
    email     = serializers.CharField()
    phone     = serializers.CharField()


class TherapistSummarySerializer(serializers.Serializer):
    """Representação resumida do terapeuta para uso em nested read-only."""
    id        = serializers.IntegerField()
    full_name = serializers.CharField()
    email     = serializers.CharField()
    specialty = serializers.CharField()


# ─────────────────────────────────────────────────────────────────────────────
# 1. AppointmentListSerializer – listagem resumida
# ─────────────────────────────────────────────────────────────────────────────

class AppointmentListSerializer(serializers.ModelSerializer):
    """
    Serializer leve para listagem de consultas.
    Expõe apenas os campos essenciais para exibição em calendários e listas.
    """
    patient_name   = serializers.CharField(source="patient.full_name", read_only=True)
    therapist_name = serializers.CharField(source="therapist.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    duration_display = serializers.CharField(read_only=True)

    class Meta:
        model  = Appointment
        fields = [
            "id",
            "patient_name",
            "therapist_name",
            "start_time",
            "end_time",
            "duration_display",
            "status",
            "status_display",
            "session_value",
            "is_recurring",
        ]


# ─────────────────────────────────────────────────────────────────────────────
# 2. AppointmentDetailSerializer – detalhamento completo
# ─────────────────────────────────────────────────────────────────────────────

class AppointmentDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para a tela de detalhe de uma consulta.
    Patient e Therapist são nested e somente-leitura.
    """
    patient          = PatientSummarySerializer(read_only=True)
    therapist        = TherapistSummarySerializer(read_only=True)
    status_display   = serializers.CharField(source="get_status_display", read_only=True)
    duration_display = serializers.CharField(read_only=True)

    # Série de recorrências relacionadas (somente leitura, sem detalhes internos)
    recurrences_count = serializers.SerializerMethodField()
    evolution_id = serializers.SerializerMethodField()
    evolution_status = serializers.SerializerMethodField()

    class Meta:
        model  = Appointment
        fields = [
            "id",
            "patient",
            "therapist",
            "start_time",
            "end_time",
            "duration_minutes",
            "duration_display",
            "status",
            "status_display",
            "notes",
            "cancellation_reason",
            "session_value",
            "is_recurring",
            "recurrence_rule",
            "parent_appointment",
            "recurrences_count",
            "evolution_id",
            "evolution_status",
            "created_at",
            "updated_at",
        ]

    def get_recurrences_count(self, obj) -> int:
        """Retorna quantas ocorrências futuras existem nesta série."""
        return obj.recurrences.count()

    def get_evolution_id(self, obj):
        try:
            return obj.evolution.id
        except Exception:
            return None

    def get_evolution_status(self, obj):
        try:
            return obj.evolution.clinical_data.status
        except Exception:
            return None



# ─────────────────────────────────────────────────────────────────────────────
# 3. AppointmentCreateSerializer – criação com validações de negócio
# ─────────────────────────────────────────────────────────────────────────────

class AppointmentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criar uma nova consulta.

    Validações aplicadas:
      1. start_time deve ser anterior a end_time.
      2. Não pode haver choque de horário com outra consulta do terapeuta.
      3. O horário deve estar dentro dos WorkingHours configurados pelo terapeuta.
      4. O terapeuta é preenchido automaticamente com request.user.

    Se is_recurring=True, a view deve chamar create_recurrences() para gerar
    as ocorrências futuras (delegado à ViewSet.perform_create).
    """

    class Meta:
        model  = Appointment
        fields = [
            "patient",
            "start_time",
            "end_time",
            "notes",
            "session_value",
            "is_recurring",
            "recurrence_rule",
        ]

    # ── Validações de campo individual ────────────────────────────────────────

    def validate_start_time(self, value):
        """Impede agendamentos no passado."""
        if value < timezone.now():
            raise serializers.ValidationError(
                "Não é possível agendar uma consulta no passado."
            )
        return value

    def validate_session_value(self, value):
        """Garante que o valor da sessão seja positivo."""
        if value < 0:
            raise serializers.ValidationError(
                "O valor da sessão não pode ser negativo."
            )
        return value

    # ── Validação cruzada entre campos ────────────────────────────────────────

    def validate(self, attrs):
        """
        Validações que dependem de múltiplos campos:
          1. start_time < end_time
          2. Ausência de choque de horários
          3. Dentro dos horários de atendimento do terapeuta
          4. Se recorrente, recurrence_rule obrigatório
        """
        start_time = attrs.get("start_time")
        end_time   = attrs.get("end_time")
        request    = self.context["request"]
        therapist  = request.user

        # 1. Validar ordem dos horários
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError(
                {"end_time": "O horário de término deve ser posterior ao de início."}
            )

        # 2. Verificar choque de horário
        exclude_id = self.instance.pk if self.instance else None
        if start_time and end_time:
            if Appointment.check_conflict(therapist, start_time, end_time, exclude_id=exclude_id):
                raise serializers.ValidationError(
                    {
                        "start_time": (
                            "Conflito de horário: já existe uma consulta agendada ou confirmada "
                            "neste intervalo para este terapeuta."
                        )
                    }
                )

        # 3. Verificar horário de atendimento configurado
        if start_time and end_time:
            self._validate_working_hours(therapist, start_time, end_time)

        # 4. Recorrência exige regra
        if attrs.get("is_recurring") and not attrs.get("recurrence_rule"):
            raise serializers.ValidationError(
                {"recurrence_rule": "Informe a regra de recorrência (WEEKLY, BIWEEKLY ou MONTHLY)."}
            )

        return attrs

    def _validate_working_hours(self, therapist, start_time: datetime, end_time: datetime):
        """
        Verifica se o horário da consulta está dentro dos horários de
        atendimento configurados pelo terapeuta para o dia da semana.
        Levanta ValidationError se fora do expediente.
        """
        # weekday(): 0=segunda ... 6=domingo
        weekday = start_time.weekday()

        working = WorkingHours.objects.filter(
            therapist=therapist,
            weekday=weekday,
            is_active=True,
        ).first()

        if working is None:
            # Terapeuta ainda não configurou horários de atendimento para este dia.
            # Permitir o agendamento; a validação só se aplica quando há regra cadastrada.
            return

        appt_start = start_time.time()
        appt_end   = end_time.time()

        if appt_start < working.start_time or appt_end > working.end_time:
            raise serializers.ValidationError(
                {
                    "start_time": (
                        f"O horário solicitado ({appt_start.strftime('%H:%M')}–{appt_end.strftime('%H:%M')}) "
                        f"está fora do expediente do terapeuta neste dia "
                        f"({working.start_time.strftime('%H:%M')}–{working.end_time.strftime('%H:%M')})."
                    )
                }
            )

    def create(self, validated_data):
        """
        Cria a consulta principal associando o terapeuta a partir do request.
        O valor padrão da sessão é herdado do perfil do terapeuta caso não
        seja informado explicitamente (já tratado no frontend, mas como fallback).
        """
        request   = self.context["request"]
        therapist = request.user

        # Atribui o terapeuta automaticamente
        validated_data["therapist"] = therapist

        # Fallback: se valor não informado, usa o valor padrão do terapeuta
        if not validated_data.get("session_value"):
            validated_data["session_value"] = therapist.default_session_value

        appointment = Appointment.objects.create(**validated_data)
        return appointment

    def create_recurrences(self, parent: Appointment, num_weeks: int = 4) -> list:
        """
        Gera ocorrências futuras a partir de uma consulta recorrente.

        Parâmetros:
            parent    : consulta-pai já criada
            num_weeks : número de semanas à frente para gerar (padrão: 4)

        Retorna lista com as ocorrências criadas.
        Chamado externamente pelo perform_create da ViewSet.
        """
        if not parent.is_recurring or not parent.recurrence_rule:
            return []

        # Define o delta entre ocorrências conforme a regra
        delta_map = {
            Appointment.RecurrenceRule.WEEKLY:   timedelta(weeks=1),
            Appointment.RecurrenceRule.BIWEEKLY: timedelta(weeks=2),
            Appointment.RecurrenceRule.MONTHLY:  timedelta(days=30),
        }
        delta = delta_map.get(parent.recurrence_rule)
        if delta is None:
            return []

        created = []
        current_start = parent.start_time
        current_end   = parent.end_time
        duration      = current_end - current_start

        for _ in range(num_weeks):
            current_start += delta
            current_end    = current_start + duration

            # Pula se houver conflito na ocorrência recorrente
            if Appointment.check_conflict(parent.therapist, current_start, current_end):
                logger.warning(
                    "Recorrência ignorada por conflito: terapeuta=%s, início=%s",
                    parent.therapist_id,
                    current_start,
                )
                continue

            recurrence = Appointment.objects.create(
                patient=parent.patient,
                therapist=parent.therapist,
                start_time=current_start,
                end_time=current_end,
                notes=parent.notes,
                session_value=parent.session_value,
                status=Appointment.Status.SCHEDULED,
                is_recurring=True,
                recurrence_rule=parent.recurrence_rule,
                parent_appointment=parent,
            )
            created.append(recurrence)

        return created


# ─────────────────────────────────────────────────────────────────────────────
# 4. AppointmentUpdateSerializer – atualização de campos da consulta
# ─────────────────────────────────────────────────────────────────────────────

class AppointmentUpdateSerializer(serializers.ModelSerializer):
    """
    Permite alterar dados de uma consulta já existente (partial=True aceito).
    Reutiliza as mesmas validações de choque de horário e working hours.
    """

    class Meta:
        model  = Appointment
        fields = [
            "patient",
            "start_time",
            "end_time",
            "notes",
            "session_value",
        ]

    def validate(self, attrs):
        """Reaplica validações de horário no update."""
        start_time = attrs.get("start_time", self.instance.start_time if self.instance else None)
        end_time   = attrs.get("end_time",   self.instance.end_time   if self.instance else None)
        request    = self.context["request"]
        therapist  = request.user

        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError(
                    {"end_time": "O horário de término deve ser posterior ao de início."}
                )
            exclude_id = self.instance.pk if self.instance else None
            if Appointment.check_conflict(therapist, start_time, end_time, exclude_id=exclude_id):
                raise serializers.ValidationError(
                    {
                        "start_time": (
                            "Conflito de horário: já existe uma consulta agendada ou confirmada "
                            "neste intervalo."
                        )
                    }
                )
        return attrs


# ─────────────────────────────────────────────────────────────────────────────
# 5. AppointmentStatusUpdateSerializer – atualização restrita de status
# ─────────────────────────────────────────────────────────────────────────────

class AppointmentStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer específico para a ação de atualização de status.
    Permite alterar apenas `status` e `cancellation_reason`.

    Regras de transição:
      - cancellation_reason obrigatório ao cancelar.
      - Não é possível reverter de 'cancelled' ou 'missed'.
    """

    class Meta:
        model  = Appointment
        fields = ["status", "cancellation_reason"]

    STATUSES_FINAIS = {Appointment.Status.CANCELLED, Appointment.Status.MISSED}

    def validate(self, attrs):
        new_status = attrs.get("status")
        instance   = self.instance

        # Impede reversão de status final
        if instance and instance.status in self.STATUSES_FINAIS:
            raise serializers.ValidationError(
                {
                    "status": (
                        f"Não é possível alterar o status de uma consulta "
                        f"já '{instance.get_status_display()}'."
                    )
                }
            )

        # Cancelamento exige motivo
        if new_status == Appointment.Status.CANCELLED:
            if not attrs.get("cancellation_reason", "").strip():
                raise serializers.ValidationError(
                    {"cancellation_reason": "Informe o motivo do cancelamento."}
                )

        return attrs


# ─────────────────────────────────────────────────────────────────────────────
# 6. CheckAvailabilitySerializer – verificação de slots disponíveis
# ─────────────────────────────────────────────────────────────────────────────

class CheckAvailabilitySerializer(serializers.Serializer):
    """
    Input serializer para verificação de horários disponíveis em uma data.

    Parâmetros de entrada:
        date     : data a consultar (YYYY-MM-DD)
        duration : duração desejada em minutos (padrão: 50)

    Saída (gerada pela view):
        Lista de dicionários com 'start' e 'end' para cada slot disponível.
    """

    date = serializers.DateField(
        help_text="Data a verificar disponibilidade (YYYY-MM-DD).",
    )
    duration = serializers.IntegerField(
        default=50,
        min_value=15,
        max_value=240,
        help_text="Duração desejada da sessão em minutos (15–240).",
    )

    def validate_date(self, value: date) -> date:
        """Impede consulta de datas passadas."""
        if value < timezone.localdate():
            raise serializers.ValidationError(
                "Não é possível verificar disponibilidade em datas passadas."
            )
        return value

    def get_available_slots(self, therapist, validated_data: dict) -> list:
        """
        Calcula e retorna os slots disponíveis para o terapeuta na data informada.

        Algoritmo:
          1. Busca os WorkingHours do terapeuta para o dia da semana.
          2. Gera slots de `duration` minutos dentro do expediente.
          3. Remove slots que conflitam com consultas já agendadas/confirmadas.

        Retorna lista de dicts: [{'start': '09:00', 'end': '09:50'}, ...]
        """
        target_date = validated_data["date"]
        duration    = validated_data["duration"]
        weekday     = target_date.weekday()

        working = WorkingHours.objects.filter(
            therapist=therapist,
            weekday=weekday,
            is_active=True,
        ).first()

        if working is None:
            return []

        # Gera todos os slots possíveis dentro do expediente
        slot_duration = timedelta(minutes=duration)
        slots = []

        tz         = timezone.get_current_timezone()
        slot_start = datetime.combine(target_date, working.start_time, tzinfo=tz)
        day_end    = datetime.combine(target_date, working.end_time,   tzinfo=tz)

        while slot_start + slot_duration <= day_end:
            slot_end = slot_start + slot_duration

            # Verifica se o slot está livre
            if not Appointment.check_conflict(therapist, slot_start, slot_end):
                slots.append(
                    {
                        "start": slot_start.strftime("%H:%M"),
                        "end":   slot_end.strftime("%H:%M"),
                        "start_datetime": slot_start.isoformat(),
                        "end_datetime":   slot_end.isoformat(),
                    }
                )

            # Avança para o próximo slot (sem gap, slots consecutivos)
            slot_start = slot_end

        return slots
