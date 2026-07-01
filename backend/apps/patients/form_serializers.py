from datetime import date
from pathlib import Path

from rest_framework import serializers

from .models import Patient
from .patient_professionals import serialize_patient_professionals
from .serializers import PatientCreateUpdateSerializer


class PatientFormSerializer(PatientCreateUpdateSerializer):
    """Contrato completo utilizado pelo drawer de criação e edição."""

    photo = serializers.FileField(required=False, allow_null=True)
    remove_photo = serializers.BooleanField(write_only=True, required=False)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=32),
        required=False,
        allow_empty=True,
    )
    professionals = serializers.SerializerMethodField(read_only=True)

    class Meta(PatientCreateUpdateSerializer.Meta):
        fields = list(
            dict.fromkeys(
                PatientCreateUpdateSerializer.Meta.fields
                + [
                    "social_name",
                    "photo",
                    "remove_photo",
                    "rg",
                    "treatment_start_date",
                    "marital_status",
                    "profession",
                    "social_network",
                    "whatsapp",
                    "attendance_type",
                    "modality",
                    "payer_type",
                    "insurance_name",
                    "session_value",
                    "planned_frequency",
                    "reminders_enabled",
                    "reminder_recipient",
                    "tags",
                    "emergency_contact_name",
                    "emergency_contact_relationship",
                    "emergency_contact_phone",
                    "guardian_phone",
                    "guardian_email",
                    "guardian_relationship",
                    "financial_responsible_name",
                    "financial_responsible_cpf",
                    "financial_responsible_phone",
                    "financial_responsible_email",
                    "financial_responsible_marital_status",
                    "financial_responsible_naturality",
                    "financial_responsible_occupation",
                    "financial_responsible_relationship",
                    "consent_terms_accepted",
                    "professionals",
                ]
            )
        )

    def get_professionals(self, obj):
        return serialize_patient_professionals(obj)

    def validate_photo(self, uploaded):
        if not uploaded:
            return uploaded
        if uploaded.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("A foto deve possuir no máximo 2 MB.")
        content_type = getattr(uploaded, "content_type", "")
        suffix = Path(uploaded.name).suffix.lower()
        if content_type not in {"image/jpeg", "image/png"} or suffix not in {
            ".jpg",
            ".jpeg",
            ".png",
        }:
            raise serializers.ValidationError("Envie uma imagem JPG ou PNG válida.")
        return uploaded

    def validate_tags(self, values):
        normalized = []
        for value in values:
            tag = value.strip()
            if tag and tag.casefold() not in {item.casefold() for item in normalized}:
                normalized.append(tag)
        if len(normalized) > 12:
            raise serializers.ValidationError("Utilize no máximo 12 etiquetas.")
        return normalized

    def validate_financial_responsible_cpf(self, value):
        return self.validate_guardian_cpf(value)

    def validate(self, attrs):
        attrs = super().validate(attrs)
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
        if birth_date and birth_date > date.today():
            raise serializers.ValidationError(
                {"birth_date": "A data de nascimento não pode estar no futuro."}
            )

        treatment_start = attrs.get(
            "treatment_start_date",
            self.instance.treatment_start_date if self.instance else None,
        )
        if treatment_start and treatment_start > date.today():
            raise serializers.ValidationError(
                {"treatment_start_date": "A data não pode estar no futuro."}
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
            raise serializers.ValidationError({"insurance_name": "Informe o convênio."})

        recipient = attrs.get(
            "reminder_recipient",
            self.instance.reminder_recipient
            if self.instance
            else Patient.ReminderRecipient.PATIENT,
        )
        if recipient in {
            Patient.ReminderRecipient.FINANCIAL_RESPONSIBLE,
            Patient.ReminderRecipient.BOTH,
        }:
            name = attrs.get(
                "financial_responsible_name",
                self.instance.financial_responsible_name if self.instance else "",
            )
            phone = attrs.get(
                "financial_responsible_phone",
                self.instance.financial_responsible_phone if self.instance else "",
            )
            errors = {}
            if not name:
                errors["financial_responsible_name"] = "Informe o responsável financeiro."
            if not phone:
                errors["financial_responsible_phone"] = "Informe o telefone do responsável."
            if errors:
                raise serializers.ValidationError(errors)

        if attrs.get("email"):
            attrs["email"] = attrs["email"].strip().lower()
        if attrs.get("full_name"):
            attrs["full_name"] = " ".join(attrs["full_name"].split())
        if attrs.get("social_name"):
            attrs["social_name"] = " ".join(attrs["social_name"].split())
        return attrs

    def create(self, validated_data):
        validated_data.pop("remove_photo", None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        remove_photo = validated_data.pop("remove_photo", False)
        patient = super().update(instance, validated_data)
        if remove_photo:
            patient.photo = None
            patient.save(update_fields=["photo", "updated_at"])
        return patient
