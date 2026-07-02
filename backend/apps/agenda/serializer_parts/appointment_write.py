from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.patients.models import Patient
from apps.users.models import WorkingHours
from ..models import (
    Appointment,
    AppointmentRecurrence,
    PatientPackage,
    Room,
    TelemedicineRoom,
)
from ..services import create_appointment_resources, generate_recurrence_appointments

User = get_user_model()


class AppointmentValidationMixin:
    def _resolve_therapist(self, attrs):
        request = self.context["request"]
        patient = attrs.get("patient", getattr(self.instance, "patient", None))
        therapist = attrs.get("therapist", getattr(self.instance, "therapist", None))
        if request.user.is_therapist:
            therapist = request.user
            attrs["therapist"] = therapist
        elif not therapist and patient:
            therapist = patient.therapist
            attrs["therapist"] = therapist
        if not therapist or not therapist.is_therapist:
            raise serializers.ValidationError(
                {"therapist": "Selecione um terapeuta válido."}
            )
        return therapist

    def _validate_business_rules(self, attrs):
        therapist = self._resolve_therapist(attrs)
        patient = attrs.get("patient", getattr(self.instance, "patient", None))
        participants = attrs.get("participants", [])
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        room = attrs.get("room", getattr(self.instance, "room", None))
        modality = attrs.get(
            "modality",
            getattr(self.instance, "modality", Appointment.Modality.IN_PERSON),
        )

        if not patient or patient.deleted_at or not patient.is_active:
            raise serializers.ValidationError(
                {"patient": "Selecione um paciente ativo."}
            )
        if patient.therapist_id != therapist.id:
            raise serializers.ValidationError(
                {"patient": "O paciente não pertence ao profissional selecionado."}
            )
        if any(item.therapist_id != therapist.id for item in participants):
            raise serializers.ValidationError(
                {"participants": "Todos os participantes devem pertencer ao profissional."}
            )
        if start and end and start >= end:
            raise serializers.ValidationError(
                {"end_time": "O término deve ser posterior ao início."}
            )
        if (
            start
            and start < timezone.now()
            and not self.context["request"].user.is_admin_role
        ):
            raise serializers.ValidationError(
                {"start_time": "Não é possível agendar no passado."}
            )
        if modality == Appointment.Modality.ONLINE and room:
            raise serializers.ValidationError(
                {"room": "Consultas online não utilizam sala física."}
            )
        if room and room.therapist_id != therapist.id:
            raise serializers.ValidationError(
                {"room": "A sala não pertence ao profissional selecionado."}
            )

        if start and end:
            conflicts = Appointment.conflict_details(
                therapist=therapist,
                patient=patient,
                start_time=start,
                end_time=end,
                room=room,
                participants=participants,
                exclude_id=getattr(self.instance, "pk", None),
            )
            if any(conflicts.values()):
                labels = {
                    "therapist": "profissional",
                    "patient": "paciente",
                    "room": "sala",
                    "block": "bloqueio de agenda",
                }
                active = [labels[key] for key, value in conflicts.items() if value]
                raise serializers.ValidationError(
                    {"start_time": f"Conflito de horário com: {', '.join(active)}."}
                )
            self._validate_working_hours(therapist, start, end)
        return attrs

    @staticmethod
    def _validate_working_hours(therapist, start, end):
        working = WorkingHours.objects.filter(
            therapist=therapist,
            weekday=start.weekday(),
            is_active=True,
        ).first()
        if working and (
            start.time() < working.start_time or end.time() > working.end_time
        ):
            raise serializers.ValidationError(
                {
                    "start_time": (
                        f"Horário fora do expediente "
                        f"({working.start_time:%H:%M}–{working.end_time:%H:%M})."
                    )
                }
            )


class AppointmentCreateSerializer(
    AppointmentValidationMixin, serializers.ModelSerializer
):
    participants = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.filter(is_active=True), many=True, required=False
    )
    therapist = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role="therapist"), required=False
    )
    room = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    package = serializers.PrimaryKeyRelatedField(
        queryset=PatientPackage.objects.all(), required=False, allow_null=True
    )
    send_whatsapp_reminder = serializers.BooleanField(
        write_only=True, default=False
    )
    recurrence_frequency = serializers.ChoiceField(
        choices=AppointmentRecurrence.Frequency.choices,
        write_only=True,
        required=False,
    )
    recurrence_interval = serializers.IntegerField(
        write_only=True, required=False, default=1, min_value=1, max_value=12
    )
    recurrence_weekdays = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=6),
        write_only=True,
        required=False,
        default=list,
    )
    recurrence_ends_on = serializers.DateField(
        write_only=True, required=False, allow_null=True
    )
    recurrence_max_occurrences = serializers.IntegerField(
        write_only=True, required=False, min_value=2, max_value=365
    )
    recurrence_conflict_strategy = serializers.ChoiceField(
        choices=["error", "skip"],
        write_only=True,
        required=False,
        default="error",
    )

    class Meta:
        model = Appointment
        fields = [
            "patient",
            "participants",
            "therapist",
            "start_time",
            "end_time",
            "modality",
            "appointment_type",
            "room",
            "session_value",
            "notes",
            "package",
            "is_recurring",
            "send_whatsapp_reminder",
            "recurrence_frequency",
            "recurrence_interval",
            "recurrence_weekdays",
            "recurrence_ends_on",
            "recurrence_max_occurrences",
            "recurrence_conflict_strategy",
        ]

    def validate(self, attrs):
        attrs = self._validate_business_rules(attrs)
        if attrs.get("session_value", Decimal("0")) < 0:
            raise serializers.ValidationError(
                {"session_value": "O valor não pode ser negativo."}
            )
        if attrs.get("is_recurring") and not attrs.get("recurrence_frequency"):
            raise serializers.ValidationError(
                {"recurrence_frequency": "Informe a frequência."}
            )
        package = attrs.get("package")
        if package and not package.can_consume():
            raise serializers.ValidationError(
                {"package": "O pacote está sem saldo, expirado ou inativo."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        participants = validated_data.pop("participants", [])
        remind = validated_data.pop("send_whatsapp_reminder", False)
        frequency = validated_data.pop("recurrence_frequency", None)
        interval = validated_data.pop("recurrence_interval", 1)
        weekdays = validated_data.pop("recurrence_weekdays", [])
        ends_on = validated_data.pop("recurrence_ends_on", None)
        max_occurrences = validated_data.pop("recurrence_max_occurrences", None)
        conflict_strategy = validated_data.pop(
            "recurrence_conflict_strategy", "error"
        )
        package = validated_data.get("package")
        request = self.context["request"]
        validated_data["created_by"] = request.user
        validated_data["updated_by"] = request.user

        recurrence = None
        if validated_data.get("is_recurring"):
            local_start = timezone.localtime(validated_data["start_time"])
            recurrence = AppointmentRecurrence.objects.create(
                patient=validated_data["patient"],
                therapist=validated_data["therapist"],
                frequency=frequency,
                interval=interval,
                weekdays=weekdays,
                starts_on=local_start.date(),
                ends_on=ends_on,
                max_occurrences=max_occurrences or 12,
                start_time=local_start.time().replace(tzinfo=None),
                duration_minutes=int(
                    (
                        validated_data["end_time"]
                        - validated_data["start_time"]
                    ).total_seconds()
                    // 60
                ),
                timezone_name=str(timezone.get_current_timezone()),
                modality=validated_data.get(
                    "modality", Appointment.Modality.IN_PERSON
                ),
                appointment_type=validated_data.get(
                    "appointment_type",
                    Appointment.AppointmentType.PSYCHOTHERAPY,
                ),
                room=validated_data.get("room"),
                session_value=validated_data["session_value"],
                notes=validated_data.get("notes", ""),
                created_by=request.user,
            )
            validated_data["recurrence"] = recurrence
            validated_data["origin"] = Appointment.Origin.RECURRENCE

        appointment = Appointment.objects.create(**validated_data)
        appointment.participants.set(participants)
        create_appointment_resources(
            appointment,
            send_whatsapp_reminder=remind,
            package=package,
        )
        if recurrence:
            generate_recurrence_appointments(
                recurrence,
                first_appointment=appointment,
                conflict_strategy=conflict_strategy,
                send_whatsapp_reminder=remind,
                package=package,
            )
        return appointment


class AppointmentUpdateSerializer(
    AppointmentValidationMixin, serializers.ModelSerializer
):
    participants = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.filter(is_active=True), many=True, required=False
    )
    therapist = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role="therapist"), required=False
    )
    room = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Appointment
        fields = [
            "patient",
            "participants",
            "therapist",
            "start_time",
            "end_time",
            "modality",
            "appointment_type",
            "room",
            "session_value",
            "notes",
        ]

    def validate(self, attrs):
        return self._validate_business_rules(attrs)

    def update(self, instance, validated_data):
        participants = validated_data.pop("participants", None)
        instance.updated_by = self.context["request"].user
        instance = super().update(instance, validated_data)
        if participants is not None:
            instance.participants.set(participants)
        if instance.modality in {
            Appointment.Modality.ONLINE,
            Appointment.Modality.HYBRID,
        }:
            TelemedicineRoom.objects.get_or_create(
                appointment=instance,
                defaults={
                    "expires_at": instance.end_time + timedelta(hours=2),
                    "status": TelemedicineRoom.Status.AVAILABLE,
                },
            )
        return instance


class AppointmentStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["status", "cancellation_reason"]

    def validate(self, attrs):
        status_value = attrs.get("status")
        if (
            status_value == Appointment.Status.CANCELLED
            and not attrs.get("cancellation_reason", "").strip()
        ):
            raise serializers.ValidationError(
                {"cancellation_reason": "Informe o motivo do cancelamento."}
            )
        if self.instance.status in {
            Appointment.Status.COMPLETED,
            Appointment.Status.MISSED,
        }:
            raise serializers.ValidationError(
                {
                    "status": (
                        "Uma sessão finalizada não pode voltar para um estado anterior."
                    )
                }
            )
        return attrs
