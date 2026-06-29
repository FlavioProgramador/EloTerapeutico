from .serializers import PatientCreateUpdateSerializer


class PatientFormSerializer(PatientCreateUpdateSerializer):
    class Meta(PatientCreateUpdateSerializer.Meta):
        fields = PatientCreateUpdateSerializer.Meta.fields + [
            "social_name",
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
        ]
