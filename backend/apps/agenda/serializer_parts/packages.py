from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from ..models import Appointment, AppointmentRecurrence, PatientPackage, Room
from ..services import create_appointment_resources, generate_recurrence_appointments
from .summary import PackageSessionSerializer


class PatientPackageSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.display_name", read_only=True)
    therapist_name = serializers.CharField(source="therapist.full_name", read_only=True)
    remaining_sessions = serializers.IntegerField(read_only=True)
    unit_value = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    sessions = PackageSessionSerializer(source="package_sessions", many=True, read_only=True)
    auto_schedule = serializers.BooleanField(write_only=True, default=False)
    first_appointment_at = serializers.DateTimeField(write_only=True, required=False)
    frequency = serializers.ChoiceField(
        choices=AppointmentRecurrence.Frequency.choices,
        write_only=True,
        required=False,
        default=AppointmentRecurrence.Frequency.WEEKLY,
    )
    weekdays = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=6),
        write_only=True,
        required=False,
        default=list,
    )
    duration_minutes = serializers.IntegerField(
        write_only=True, required=False, default=50, min_value=15, max_value=240
    )
    modality = serializers.ChoiceField(
        choices=Appointment.Modality.choices,
        write_only=True,
        required=False,
        default=Appointment.Modality.IN_PERSON,
    )
    appointment_type = serializers.ChoiceField(
        choices=Appointment.AppointmentType.choices,
        write_only=True,
        required=False,
        default=Appointment.AppointmentType.PSYCHOTHERAPY,
    )
    room = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.filter(is_active=True),
        write_only=True,
        required=False,
        allow_null=True,
    )
    send_whatsapp_reminder = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = PatientPackage
        fields = [
            "id",
            "patient",
            "patient_name",
            "therapist",
            "therapist_name",
            "name",
            "description",
            "sessions_contracted",
            "sessions_used",
            "remaining_sessions",
            "total_value",
            "unit_value",
            "valid_from",
            "valid_until",
            "status",
            "is_expired",
            "generate_charge",
            "send_charge",
            "sessions",
            "auto_schedule",
            "first_appointment_at",
            "frequency",
            "weekdays",
            "duration_minutes",
            "modality",
            "appointment_type",
            "room",
            "send_whatsapp_reminder",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["sessions_used", "created_at", "updated_at"]

    def validate(self, attrs):
        request = self.context["request"]
        patient = attrs.get("patient", getattr(self.instance, "patient", None))
        therapist = attrs.get("therapist", getattr(self.instance, "therapist", None))
        if request.user.is_therapist:
            therapist = request.user
            attrs["therapist"] = therapist
        if not therapist or not therapist.is_therapist:
            raise serializers.ValidationError({"therapist": "Selecione um terapeuta válido."})
        if patient and patient.therapist_id != therapist.id:
            raise serializers.ValidationError({"patient": "O paciente não pertence ao profissional selecionado."})
        sessions = attrs.get("sessions_contracted", getattr(self.instance, "sessions_contracted", 0))
        if sessions <= 0:
            raise serializers.ValidationError({"sessions_contracted": "Informe ao menos uma sessão."})
        if attrs.get("total_value", Decimal("0")) < 0:
            raise serializers.ValidationError({"total_value": "O valor total não pode ser negativo."})
        valid_from = attrs.get("valid_from", getattr(self.instance, "valid_from", timezone.localdate()))
        valid_until = attrs.get("valid_until", getattr(self.instance, "valid_until", None))
        if valid_until and valid_until < valid_from:
            raise serializers.ValidationError({"valid_until": "A validade final deve ser posterior ao início."})
        if attrs.get("auto_schedule") and not attrs.get("first_appointment_at"):
            raise serializers.ValidationError({"first_appointment_at": "Informe a primeira data do pacote."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        auto_schedule = validated_data.pop("auto_schedule", False)
        first_at = validated_data.pop("first_appointment_at", None)
        frequency = validated_data.pop("frequency", AppointmentRecurrence.Frequency.WEEKLY)
        weekdays = validated_data.pop("weekdays", [])
        duration = validated_data.pop("duration_minutes", 50)
        modality = validated_data.pop("modality", Appointment.Modality.IN_PERSON)
        appointment_type = validated_data.pop("appointment_type", Appointment.AppointmentType.PSYCHOTHERAPY)
        room = validated_data.pop("room", None)
        remind = validated_data.pop("send_whatsapp_reminder", False)
        request = self.context["request"]
        validated_data["created_by"] = request.user
        package = super().create(validated_data)

        if package.generate_charge:
            from apps.financeiro.models import FinancialTransaction

            FinancialTransaction.objects.create(
                therapist=package.therapist,
                patient=package.patient,
                transaction_type=FinancialTransaction.TransactionType.INCOME,
                category=FinancialTransaction.Category.SUBSCRIPTION,
                amount=package.total_value,
                payment_status=FinancialTransaction.PaymentStatus.PENDING,
                due_date=package.valid_from,
                description=f"Pacote {package.name}",
            )

        if auto_schedule and first_at:
            rule = AppointmentRecurrence.objects.create(
                patient=package.patient,
                therapist=package.therapist,
                frequency=frequency,
                weekdays=weekdays,
                starts_on=first_at.date(),
                max_occurrences=package.sessions_contracted,
                start_time=timezone.localtime(first_at).time().replace(tzinfo=None),
                duration_minutes=duration,
                modality=modality,
                appointment_type=appointment_type,
                room=room,
                session_value=package.unit_value,
                created_by=request.user,
            )
            conflicts = Appointment.conflict_details(
                therapist=package.therapist,
                patient=package.patient,
                start_time=first_at,
                end_time=first_at + timedelta(minutes=duration),
                room=room,
            )
            if any(conflicts.values()):
                raise serializers.ValidationError({"first_appointment_at": "A primeira sessão possui conflito."})
            first = Appointment.objects.create(
                patient=package.patient,
                therapist=package.therapist,
                start_time=first_at,
                end_time=first_at + timedelta(minutes=duration),
                modality=modality,
                appointment_type=appointment_type,
                room=room,
                session_value=package.unit_value,
                is_recurring=True,
                recurrence=rule,
                package=package,
                origin=Appointment.Origin.PACKAGE,
                created_by=request.user,
                updated_by=request.user,
            )
            create_appointment_resources(first, send_whatsapp_reminder=remind, package=package)
            generate_recurrence_appointments(
                rule,
                first_appointment=first,
                conflict_strategy="error",
                send_whatsapp_reminder=remind,
                package=package,
            )
        return package
