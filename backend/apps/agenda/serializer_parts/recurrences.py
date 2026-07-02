from django.utils import timezone
from rest_framework import serializers

from ..models import Appointment, AppointmentRecurrence


class AppointmentRecurrenceSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.display_name", read_only=True)
    therapist_name = serializers.CharField(source="therapist.full_name", read_only=True)
    frequency_display = serializers.CharField(source="get_frequency_display", read_only=True)
    occurrences_count = serializers.IntegerField(source="appointments.count", read_only=True)
    completed_count = serializers.SerializerMethodField()
    next_occurrence_id = serializers.SerializerMethodField()
    next_occurrence_at = serializers.SerializerMethodField()

    class Meta:
        model = AppointmentRecurrence
        fields = [
            "id", "patient", "patient_name", "therapist", "therapist_name",
            "frequency", "frequency_display", "interval", "weekdays", "starts_on",
            "ends_on", "max_occurrences", "start_time", "duration_minutes",
            "timezone_name", "modality", "appointment_type", "room",
            "session_value", "notes", "status", "occurrences_count",
            "completed_count", "next_occurrence_id", "next_occurrence_at",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_completed_count(self, obj):
        return obj.appointments.filter(status=Appointment.Status.COMPLETED).count()

    def _next(self, obj):
        return obj.appointments.filter(
            start_time__gte=timezone.now(),
            status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED],
        ).order_by("start_time").first()

    def get_next_occurrence_id(self, obj):
        item = self._next(obj)
        return item.id if item else None

    def get_next_occurrence_at(self, obj):
        item = self._next(obj)
        return item.start_time if item else None
