"""Contratos da experiência ampliada de pacientes."""

import re
from datetime import date
from pathlib import Path

from django.db import transaction
from rest_framework import serializers

from apps.core.validators import validate_cpf, validate_phone
from apps.patients.models import Patient, PatientProfessional
from apps.users.models import User


class PatientProfessionalSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="professional_id", read_only=True)
    full_name = serializers.CharField(source="professional.full_name", read_only=True)
    email = serializers.EmailField(source="professional.email", read_only=True)
    specialty = serializers.CharField(source="professional.specialty", read_only=True)

    class Meta:
        model = PatientProfessional
        fields = ["id", "full_name", "email", "specialty", "is_primary"]
        read_only_fields = fields


class PatientRepresentationMixin:
    photo_url = serializers.SerializerMethodField()
    display_name = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    masked_cpf = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    therapist_name = serializers.CharField(source="therapist.full_name", read_only=True)

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        request = self.context.get("request")
        path = f"/api/v1/patients/{obj.id}/photo/"
        return request.build_absolute_uri(path) if request else path


class PatientWorkspaceListSerializer(PatientRepresentationMixin, serializers.ModelSerializer):
    """Linha segura da listagem de pacientes."""

    class Meta:
        model = Patient
        fields = [
            "id",
            "full_name",
            "social_name",
            "display_name",
            "photo_url",
            "masked_cpf",
            "birth_date",
            "age",
            "phone",
            "whatsapp",
            "email",
            "status",
            "status_display",
            "is_active",
            "therapist",
            "therapist_name",
            "payer_type",
            "insurance_name",
            "reminders_enabled",
            "reminder_recipient",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PatientWorkspaceDetailSerializer(PatientRepresentationMixin, serializers.ModelSerializer):
    """Cadastro completo para leitura e edição no drawer."""

    formatted_cpf = serializers.CharField(read_only=True)
    professionals = PatientProfessionalSerializer(
        source="professional_links",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Patient
        fields = [
            "id",
            "full_name",
            "social_name",
            "photo_url",
            "cpf",
            "formatted_cpf",
            "masked_cpf",
            "rg",
            "birth_date",
            "treatment_start_date",
            "age",
            "gender",
            "marital_status",
            "profession",
            "social_network",
            "email",
            "phone",
            "whatsapp",
            "address",
            "therapist",
            "therapist_name",
            "professionals",
            "status",
            "status_display",
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
            "consent_at",
            "notes",
            "is_active",
            "deleted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "photo_url",
            "formatted_cpf",
            "masked_cpf",
            "therapist_name",
            "professionals",
            "status_display",
            "consent_at",
            "is_active",
            "deleted_at",
            "created_at",
            "updated_at",
            "age",
        ]


class PatientWorkspaceFormSerializer(serializers.ModelSerializer):
    """Validação do cadastro ampliado, inclusive foto e profissionais."""

    cpf = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    guardian_cpf = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    financial_responsible_cpf = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    therapist = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.THERAPIST, is_active=True),
        required=False,
    )
    professional_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        write_only=True,
    )
    photo = serializers.FileField(required=False, allow_null=True, write_only=True)

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
            "therapist",
            "professional_ids",
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
        ]
        extra_kwargs = {
            "birth_date": {"required": False, "allow_null": True},
            "address": {"required": False},
            "session_value": {"required": False},
        }

    @staticmethod
    def _clean_cpf(value):
        if not value:
            return None
        validate_cpf(value)
        return re.sub(r"\D", "", value)

    def validate_cpf(self, value):
        clean = self._clean_cpf(value)
        if not clean:
            return None
        queryset = Patient.all_objects.filter(cpf=clean)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Este CPF já está cadastrado.")
        return clean

    def validate_guardian_cpf(self, value):
        return self._clean_cpf(value) or ""

    def validate_financial_responsible_cpf(self, value):
        return self._clean_cpf(value) or ""

    def _validate_phone(self, value):
        if value:
            validate_phone(value)
        return value

    validate_phone = _validate_phone
    validate_whatsapp = _validate_phone
    validate_emergency_contact_phone = _validate_phone
    validate_guardian_phone = _validate_phone
    validate_financial_responsible_phone = _validate_phone

    def validate_photo(self, uploaded_file):
        extension = Path(uploaded_file.name).suffix.lower()
        if uploaded_file.content_type not in {
            "image/jpeg",
            "image/png",
            "image/webp",
        } or extension not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise serializers.ValidationError("Envie uma imagem JPG, PNG ou WebP.")
        if uploaded_file.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("A foto deve possuir no máximo 2 MB.")
        return uploaded_file

    def validate_professional_ids(self, values):
        unique_ids = list(dict.fromkeys(values))
        found = User.objects.filter(
            id__in=unique_ids,
            role=User.Role.THERAPIST,
            is_active=True,
        ).count()
        if found != len(unique_ids):
            raise serializers.ValidationError("Há profissionais inválidos na seleção.")
        return unique_ids

    def validate(self, attrs):
        user = self.context["request"].user
        therapist = attrs.get("therapist", getattr(self.instance, "therapist", None))
        if user.is_therapist:
            if self.instance and self.instance.therapist_id != user.id:
                raise serializers.ValidationError(
                    {"therapist": "Somente o terapeuta principal pode editar o cadastro."}
                )
            attrs["therapist"] = user
            therapist = user
        elif not therapist:
            raise serializers.ValidationError({"therapist": "Selecione o terapeuta principal."})

        birth_date = attrs.get("birth_date", getattr(self.instance, "birth_date", None))
        guardian_name = attrs.get("guardian_name", getattr(self.instance, "guardian_name", ""))
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 18 and not guardian_name:
                raise serializers.ValidationError({"guardian_name": "Informe o responsável legal do menor."})

        payer_type = attrs.get("payer_type", getattr(self.instance, "payer_type", Patient.PayerType.PRIVATE))
        insurance_name = attrs.get("insurance_name", getattr(self.instance, "insurance_name", ""))
        if payer_type == Patient.PayerType.INSURANCE and not insurance_name:
            raise serializers.ValidationError({"insurance_name": "Informe o nome do convênio."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        professional_ids = validated_data.pop("professional_ids", [])
        patient = super().create(validated_data)
        self._sync_professionals(patient, professional_ids)
        return patient

    @transaction.atomic
    def update(self, instance, validated_data):
        professional_ids = validated_data.pop("professional_ids", None)
        patient = super().update(instance, validated_data)
        if professional_ids is not None:
            self._sync_professionals(patient, professional_ids)
        return patient

    def _sync_professionals(self, patient, professional_ids):
        ids = set(professional_ids)
        ids.add(patient.therapist_id)
        existing = {link.professional_id: link for link in patient.professional_links.select_for_update()}
        for professional_id in ids:
            link = existing.get(professional_id)
            if link:
                link.is_active = True
                link.is_primary = professional_id == patient.therapist_id
                link.save(update_fields=["is_active", "is_primary"])
            else:
                PatientProfessional.objects.create(
                    patient=patient,
                    professional_id=professional_id,
                    is_primary=professional_id == patient.therapist_id,
                    assigned_by=self.context["request"].user,
                )
        patient.professional_links.exclude(professional_id__in=ids).update(is_active=False, is_primary=False)
