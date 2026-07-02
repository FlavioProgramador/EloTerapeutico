from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.patients.models import Patient
from ..models import AppointmentReminder, PackageSession, Room, TelemedicineRoom

User = get_user_model()


class PatientSummarySerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    masked_cpf = serializers.CharField(read_only=True)

    class Meta:
        model = Patient
        fields = ["id", "display_name", "full_name", "masked_cpf", "phone", "whatsapp"]


class TherapistSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "email", "specialty"]


class RoomSerializer(serializers.ModelSerializer):
    therapist_name = serializers.CharField(source="therapist.full_name", read_only=True)

    class Meta:
        model = Room
        fields = [
            "id", "therapist", "therapist_name", "name", "location", "capacity",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate_therapist(self, value):
        request = self.context["request"]
        if request.user.is_therapist and value != request.user:
            raise serializers.ValidationError("Você só pode gerenciar suas próprias salas.")
        if not value.is_therapist:
            raise serializers.ValidationError("A sala deve pertencer a um terapeuta.")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        if request.user.is_therapist:
            validated_data["therapist"] = request.user
        return super().create(validated_data)


class AppointmentReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentReminder
        fields = [
            "id", "appointment", "channel", "scheduled_for", "status",
            "recipient_masked", "error_message", "sent_at", "created_at",
        ]
        read_only_fields = fields


class TelemedicineRoomSerializer(serializers.ModelSerializer):
    patient_link = serializers.SerializerMethodField()
    professional_link = serializers.SerializerMethodField()
    is_accessible = serializers.BooleanField(read_only=True)
    appointment_start = serializers.DateTimeField(source="appointment.start_time", read_only=True)
    patient_name = serializers.CharField(source="appointment.patient.display_name", read_only=True)
    therapist_name = serializers.CharField(source="appointment.therapist.full_name", read_only=True)

    class Meta:
        model = TelemedicineRoom
        fields = [
            "id", "appointment", "appointment_start", "patient_name", "therapist_name",
            "patient_link", "professional_link", "expires_at", "status",
            "is_accessible", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def _build_link(self, role: str, token) -> str:
        request = self.context.get("request")
        path = f"/telemedicine/{role}/{token}"
        return request.build_absolute_uri(path) if request else path

    def get_patient_link(self, obj):
        return self._build_link("patient", obj.patient_token)

    def get_professional_link(self, obj):
        return self._build_link("professional", obj.professional_token)


class PackageSessionSerializer(serializers.ModelSerializer):
    appointment_status = serializers.CharField(source="appointment.status", read_only=True)

    class Meta:
        model = PackageSession
        fields = [
            "id", "package", "appointment", "appointment_status", "scheduled_for",
            "status", "consumed", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
