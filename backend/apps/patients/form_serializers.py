from datetime import date

from rest_framework import serializers

from .models import Patient
from .serializers import PatientCreateUpdateSerializer


class PatientFormSerializer(PatientCreateUpdateSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length=32),
        required=False,
        allow_empty=True,
    )

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

    def validate_tags(self, values):
        normalized = []
        for value in values:
            tag = value.strip()
            if tag and tag.casefold() not in {item.casefold() for item in normalized}:
                normalized.append(tag)
        if len(normalized) > 12:
            raise serializers.ValidationError("Utilize no máximo 12 etiquetas.")
        return normalized

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        current_therapist = self.instance.therapist if self.instance else None
        therapist = attrs.get("therapist", current_therapist)

        if user and user.is_authenticated:
            if user.is_therapist:
                if therapist and therapist != user:
                    raise serializers.ValidationError(
                        {"therapist": "Não é permitido selecionar outro profissional."}
                    )
                attrs["therapist"] = user
            elif not therapist:
                raise serializers.ValidationError(
                    {"therapist": "Selecione o terapeuta responsável."}
                )

        birth_date = attrs.get(
            "birth_date",
            self.instance.birth_date if self.instance else None,
        )
        guardian_name = attrs.get(
            "guardian_name",
            self.instance.guardian_name if self.instance else "",
        )
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - (
                (today.month, today.day) < (birth_date.month, birth_date.day)
            )
            if age < 18 and not guardian_name:
                raise serializers.ValidationError(
                    {"guardian_name": "Informe o responsável legal."}
                )

        payer_type = attrs.get(
            "payer_type",
            self.instance.payer_type if self.instance else Patient.PayerType.PRIVATE,
        )
        insurance_name = attrs.get(
            "insurance_name",
            self.instance.insurance_name if self.instance else "",
        )
        if payer_type == Patient.PayerType.INSURANCE and not insurance_name:
            raise serializers.ValidationError(
                {"insurance_name": "Informe o convênio."}
            )
        return attrs
