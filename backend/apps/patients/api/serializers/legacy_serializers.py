"""
apps/patients/serializers.py
Serializers para o modelo Patient do sistema Elo Terapêutico.
"""

import re
from datetime import date

from rest_framework import serializers

from apps.patients.models import Patient
from apps.users.models import User
from core.validators import validate_cpf, validate_phone


class PatientListSerializer(serializers.ModelSerializer):
    """Serializer resumido para listagem de pacientes."""

    age = serializers.IntegerField(read_only=True)
    formatted_cpf = serializers.CharField(read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id",
            "full_name",
            "cpf",
            "formatted_cpf",
            "phone",
            "email",
            "status",
            "age",
            "is_active",
        ]
        read_only_fields = fields


class PatientDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado com todos os campos do paciente."""

    age = serializers.IntegerField(read_only=True)
    formatted_cpf = serializers.CharField(read_only=True)
    therapist_name = serializers.CharField(source="therapist.full_name", read_only=True)

    class Meta:
        model = Patient
        fields = [
            "id",
            "full_name",
            "cpf",
            "formatted_cpf",
            "birth_date",
            "gender",
            "email",
            "phone",
            "address",
            "therapist",
            "therapist_name",
            "status",
            "referral_source",
            "guardian_name",
            "guardian_cpf",
            "notes",
            "is_active",
            "deleted_at",
            "created_at",
            "updated_at",
            "age",
        ]
        read_only_fields = [
            "id",
            "is_active",
            "deleted_at",
            "created_at",
            "updated_at",
            "age",
        ]


class FlexibleJSONField(serializers.Field):
    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value


class PatientCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer de criação e atualização com validações do domínio."""

    cpf = serializers.CharField(max_length=14, required=False, allow_blank=True, allow_null=True)
    guardian_cpf = serializers.CharField(max_length=14, required=False, allow_blank=True, allow_null=True)
    financial_responsible_cpf = serializers.CharField(max_length=14, required=False, allow_blank=True, allow_null=True)
    therapist = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.THERAPIST),
        required=False,
    )
    tags = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    # Define address as a generic field so DRF doesn't crash trying to parse it as JSON before validate()
    address = FlexibleJSONField(required=False)

    def is_valid(self, *, raise_exception=False):
        valid = super().is_valid(raise_exception=False)
        if not valid:
            print("VALIDATION ERRORS:", self.errors)
        if raise_exception and not valid:
            raise serializers.ValidationError(self.errors)
        return valid

    class Meta:
        model = Patient
        fields = [
            "full_name",
            "social_name",
            "photo",
            "cpf",
            "rg",
            "birth_date",
            "treatment_start_date",
            "gender",
            "marital_status",
            "profession",
            "social_network",
            "email",
            "phone",
            "whatsapp",
            "address",
            "status",
            "attendance_type",
            "modality",
            "payer_type",
            "insurance_name",
            "session_value",
            "planned_frequency",
            "reminders_enabled",
            "reminder_recipient",
            "referral_source",
            "tags",
            "emergency_contact_name",
            "emergency_contact_relationship",
            "emergency_contact_phone",
            "guardian_name",
            "guardian_cpf",
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
            "notes",
            "therapist",
        ]

    def validate_cpf(self, value):
        if not value:
            return value
        validate_cpf(value)
        clean_cpf = re.sub(r"\D", "", value)
        queryset = Patient.all_objects.filter(cpf=clean_cpf)
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        if queryset.exists():
            raise serializers.ValidationError("Um paciente com este CPF já está cadastrado.")
        return clean_cpf

    def validate_guardian_cpf(self, value):
        if value:
            validate_cpf(value)
            return re.sub(r"\D", "", value)
        return value

    def validate_financial_responsible_cpf(self, value):
        if value:
            validate_cpf(value)
            return re.sub(r"\D", "", value)
        return value

    def validate_phone(self, value):
        if value:
            validate_phone(value)
        return value

    def validate(self, attrs):
        import json

        address = attrs.get("address")
        if isinstance(address, str):
            try:
                attrs["address"] = json.loads(address)
            except json.JSONDecodeError:
                raise serializers.ValidationError({"address": "Endereço inválido."})
        elif address is None:
            attrs["address"] = {}

        request = self.context.get("request")
        if request and request.user:
            user = request.user
            if not user.is_therapist:
                therapist = attrs.get(
                    "therapist",
                    self.instance.therapist if self.instance else None,
                )
                if not therapist:
                    raise serializers.ValidationError(
                        {"therapist": ("O campo terapeuta é obrigatório para este perfil.")}
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
            age = today.year - birth_date.year
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1

            if age < 18 and not guardian_name:
                raise serializers.ValidationError(
                    {"guardian_name": ("Pacientes menores de 18 anos devem ter um responsável cadastrado.")}
                )

        return attrs
