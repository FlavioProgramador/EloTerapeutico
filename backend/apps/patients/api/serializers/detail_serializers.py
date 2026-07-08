from rest_framework import serializers

from apps.patients.api.serializers.legacy_serializers import PatientDetailSerializer


class PatientFullDetailSerializer(PatientDetailSerializer):
    """Detalhe completo consumido pela ficha e pelo formulário de edição."""

    masked_cpf = serializers.CharField(read_only=True)
    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta(PatientDetailSerializer.Meta):
        fields = PatientDetailSerializer.Meta.fields + [
            "social_name",
            "masked_cpf",
            "status_display",
            "rg",
            "marital_status",
            "whatsapp",
            "attendance_type",
            "modality",
            "payer_type",
            "insurance_name",
            "session_value",
            "planned_frequency",
            "tags",
            "emergency_contact_name",
            "emergency_contact_relationship",
            "emergency_contact_phone",
            "guardian_phone",
            "guardian_email",
            "guardian_relationship",
            "consent_terms_accepted",
            "consent_at",
        ]
        read_only_fields = PatientDetailSerializer.Meta.read_only_fields + [
            "masked_cpf",
            "status_display",
            "consent_at",
        ]
