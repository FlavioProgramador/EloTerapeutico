from datetime import date
from pathlib import Path

from django.db import transaction
from rest_framework import serializers

from apps.users.models import User

from .models import Patient, PatientProfessional
from .serializers import PatientCreateUpdateSerializer


class PatientFormSerializer(PatientCreateUpdateSerializer):
    """Contrato completo e seguro usado pelo drawer de criação e edição."""

    photo = serializers.FileField(required=False, allow_null=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=32),
        required=False,
        allow_empty=True,
    )
    professional_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.THERAPIST, is_active=True),
        many=True,
        write_only=True,
        required=False,
    )
    professionals = serializers.SerializerMethodField(read_only=True)

    class Meta(PatientCreateUpdateSerializer.Meta):
        fields = list(
            dict.fromkeys(
                PatientCreateUpdateSerializer.Meta.fields
                + [
                    "social_name",
                    "photo",
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
                    "professional_ids",
                    "professionals",
                ]
            )
        )

    def get_professionals(self, obj):
        links = list(
            obj.professional_links.filter(is_active=True).select_related("professional")
        )
        data = [
            {
                "id": link.professional_id,
                "full_name": link.professional.full_name,
                "is_primary": link.is_primary,
            }
            for link in links
        ]
        if obj.therapist_id and obj.therapist_id not in {item["id"] for item in data}:
            data.insert(
                0,
                {
                    "id": obj.therapist_id,
                    "full_name": obj.therapist.full_name,
                    "is_primary": True,
                },
            )
        return data

    def validate_photo(self, uploaded):
        if not uploaded:
            return uploaded
        if uploaded.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("A foto deve possuir no máximo 2 MB.")
        content_type = getattr(uploaded, "content_type", "")
        allowed_types = {"image/jpeg", "image/png"}
        allowed_suffixes = {".jpg", ".jpeg", ".png"}
        if content_type not in allowed_types or Path(uploaded.name).suffix.lower() not in allowed_suffixes:
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
        professionals = attrs.get("professional_ids")

        if user and user.is_authenticated:
            if user.is_therapist:
                if therapist and therapist != user:
                    raise serializers.ValidationError(
                        {"therapist": "Não é permitido selecionar outro profissional."}
                    )
                if professionals and any(item.pk != user.pk for item in professionals):
                    raise serializers.ValidationError(
                        {"professional_ids": "Não é permitido atribuir outros profissionais."}
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
                {"treatment_start_date": "O início do atendimento não pode estar no futuro."}
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
            responsible_name = attrs.get(
                "financial_responsible_name",
                self.instance.financial_responsible_name if self.instance else "",
            )
            responsible_phone = attrs.get(
                "financial_responsible_phone",
                self.instance.financial_responsible_phone if self.instance else "",
            )
            errors = {}
            if not responsible_name:
                errors["financial_responsible_name"] = "Informe o responsável financeiro."
            if not responsible_phone:
                errors["financial_responsible_phone"] = "Informe o telefone do responsável."
            if errors:
                raise serializers.ValidationError(errors)

        email = attrs.get("email")
        if email:
            attrs["email"] = email.strip().lower()
        full_name = attrs.get("full_name")
        if full_name:
            attrs["full_name"] = " ".join(full_name.split())
        social_name = attrs.get("social_name")
        if social_name:
            attrs["social_name"] = " ".join(social_name.split())
        return attrs

    def _sync_professionals(self, patient, professionals):
        request = self.context.get("request")
        assigned_by = request.user
        selected = {professional.pk: professional for professional in professionals or []}
        selected[patient.therapist_id] = patient.therapist

        PatientProfessional.objects.filter(patient=patient).exclude(
            professional_id__in=selected
        ).update(is_active=False, is_primary=False)

        for professional_id, professional in selected.items():
            PatientProfessional.objects.update_or_create(
                patient=patient,
                professional=professional,
                defaults={
                    "is_active": True,
                    "is_primary": professional_id == patient.therapist_id,
                    "assigned_by": assigned_by,
                },
            )

    @transaction.atomic
    def create(self, validated_data):
        professionals = validated_data.pop("professional_ids", None)
        patient = super().create(validated_data)
        self._sync_professionals(patient, professionals)
        return patient

    @transaction.atomic
    def update(self, instance, validated_data):
        professionals = validated_data.pop("professional_ids", None)
        patient = super().update(instance, validated_data)
        if professionals is not None or not patient.professional_links.exists():
            self._sync_professionals(patient, professionals)
        return patient
