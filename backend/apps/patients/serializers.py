"""
apps/patients/serializers.py
Serializers para o modelo Patient do sistema Elo Terapêutico.
"""

import re
from rest_framework import serializers
from core.validators import validate_cpf, validate_phone
from .models import Patient


from apps.users.models import User


class PatientListSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listagem de pacientes.
    """

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
    """
    Serializer detalhado com todos os campos do paciente.
    """

    age = serializers.IntegerField(read_only=True)
    formatted_cpf = serializers.CharField(read_only=True)
    therapist_name = serializers.CharField(
        source="therapist.full_name", read_only=True
    )

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


class PatientCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação e atualização de pacientes com
    validações customizadas.
    """

    cpf = serializers.CharField(max_length=14, required=True)
    guardian_cpf = serializers.CharField(
        max_length=14, required=False, allow_blank=True, allow_null=True
    )
    therapist = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.THERAPIST),
        required=False,
    )

    class Meta:
        model = Patient
        fields = [
            "full_name",
            "cpf",
            "birth_date",
            "gender",
            "email",
            "phone",
            "address",
            "status",
            "referral_source",
            "guardian_name",
            "guardian_cpf",
            "notes",
            "therapist",
        ]

    def validate_cpf(self, value):
        # Valida usando o validador do core
        validate_cpf(value)
        # Normaliza removendo não dígitos
        clean_cpf = re.sub(r"\D", "", value)

        # Verifica se já existe um paciente com este CPF
        # Exclui o próprio paciente se for uma atualização (update)
        instance = self.instance
        queryset = Patient.all_objects.filter(cpf=clean_cpf)
        if instance:
            queryset = queryset.exclude(id=instance.id)
        if queryset.exists():
            raise serializers.ValidationError(
                "Um paciente com este CPF já está cadastrado."
            )

        return clean_cpf

    def validate_guardian_cpf(self, value):
        if value:
            validate_cpf(value)
            return re.sub(r"\D", "", value)
        return value

    def validate_phone(self, value):
        if value:
            validate_phone(value)
        return value

    def validate(self, attrs):
        # Validar que o terapeuta é fornecido se o usuário não for um terapeuta
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
                        {
                            "therapist": (
                                "O campo terapeuta é obrigatório "
                                "para este perfil."
                            )
                        }
                    )

        # Valida responsável legal caso seja menor de 18 anos
        birth_date = attrs.get("birth_date")
        if birth_date:
            # Calcula idade
            from datetime import date

            today = date.today()
            birthday_this_year = birth_date.replace(year=today.year)
            age = today.year - birth_date.year
            if birthday_this_year > today:
                age -= 1

            if age < 18:
                guardian_name = attrs.get("guardian_name")
                if guardian_name is None:
                    guardian_name = (
                        self.instance.guardian_name if self.instance else ""
                    )
                if not guardian_name:
                    raise serializers.ValidationError(
                        {
                            "guardian_name": (
                                "Pacientes menores de 18 anos devem "
                                "ter um responsável cadastrado."
                            )
                        }
                    )
        return attrs
