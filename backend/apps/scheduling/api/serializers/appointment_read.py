from rest_framework import serializers

from apps.scheduling.models import Appointment, TelemedicineRoom

from .summary import (
    AppointmentReminderSerializer,
    PatientSummarySerializer,
    TelemedicineRoomSerializer,
    TherapistSummarySerializer,
)


class AppointmentListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.display_name", read_only=True)
    therapist_name = serializers.CharField(source="therapist.full_name", read_only=True)
    room_name = serializers.CharField(source="room.name", read_only=True, allow_null=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    modality_display = serializers.CharField(source="get_modality_display", read_only=True)
    type_display = serializers.CharField(source="get_appointment_type_display", read_only=True)
    telemedicine_status = serializers.SerializerMethodField()
    evolution_id = serializers.SerializerMethodField()
    evolution_status = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "patient_name",
            "therapist",
            "therapist_name",
            "start_time",
            "end_time",
            "duration_minutes",
            "duration_display",
            "status",
            "status_display",
            "modality",
            "modality_display",
            "appointment_type",
            "type_display",
            "room",
            "room_name",
            "session_value",
            "is_recurring",
            "recurrence",
            "package",
            "telemedicine_status",
            "evolution_id",
            "evolution_status",
        ]

    def get_telemedicine_status(self, obj):
        try:
            return obj.telemedicine_room.status
        except TelemedicineRoom.DoesNotExist:
            return None

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


class AppointmentDetailSerializer(AppointmentListSerializer):
    patient_data = PatientSummarySerializer(source="patient", read_only=True)
    therapist_data = TherapistSummarySerializer(source="therapist", read_only=True)
    participant_data = PatientSummarySerializer(source="participants", many=True, read_only=True)
    reminders = AppointmentReminderSerializer(many=True, read_only=True)
    telemedicine = serializers.SerializerMethodField()

    class Meta(AppointmentListSerializer.Meta):
        fields = AppointmentListSerializer.Meta.fields + [
            "patient_data",
            "therapist_data",
            "participant_data",
            "notes",
            "cancellation_reason",
            "origin",
            "parent_appointment",
            "reminders",
            "telemedicine",
            "created_at",
            "updated_at",
        ]

    def get_telemedicine(self, obj):
        try:
            return TelemedicineRoomSerializer(obj.telemedicine_room, context=self.context).data
        except TelemedicineRoom.DoesNotExist:
            return None
