from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from apps.agenda.models import Appointment, AppointmentRecurrence, PatientPackage, Room
from apps.agenda.services import create_patient_package

from .summary import PackageSessionSerializer


def _validation_detail(exc: DjangoValidationError):
    return getattr(exc, "message_dict", None) or getattr(exc, "messages", [str(exc)])


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

    def create(self, validated_data):
        try:
            return create_patient_package(
                actor=self.context["request"].user,
                validated_data=validated_data,
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(_validation_detail(exc)) from exc
