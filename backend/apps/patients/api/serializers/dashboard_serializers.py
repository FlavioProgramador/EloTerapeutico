from rest_framework import serializers

from apps.patients.models import Patient


class PatientDashboardSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    masked_cpf = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    therapist_name = serializers.CharField(source="therapist.full_name", read_only=True)
    last_session = serializers.DateTimeField(read_only=True, allow_null=True)
    next_session = serializers.DateTimeField(read_only=True, allow_null=True)
    next_session_status = serializers.CharField(read_only=True, allow_null=True)
    latest_evolution_at = serializers.DateTimeField(read_only=True, allow_null=True)
    latest_evolution_id = serializers.IntegerField(read_only=True, allow_null=True)
    total_sessions = serializers.IntegerField(read_only=True)
    missed_sessions = serializers.IntegerField(read_only=True)
    documents_count = serializers.IntegerField(read_only=True)
    active_goals_count = serializers.IntegerField(read_only=True)
    has_anamnesis = serializers.BooleanField(read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id",
            "full_name",
            "social_name",
            "display_name",
            "masked_cpf",
            "age",
            "phone",
            "whatsapp",
            "email",
            "status",
            "status_display",
            "tags",
            "therapist",
            "therapist_name",
            "attendance_type",
            "modality",
            "payer_type",
            "insurance_name",
            "last_session",
            "next_session",
            "next_session_status",
            "latest_evolution_at",
            "latest_evolution_id",
            "total_sessions",
            "missed_sessions",
            "documents_count",
            "active_goals_count",
            "has_anamnesis",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
