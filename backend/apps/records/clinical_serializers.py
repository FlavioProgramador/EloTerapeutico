"""Serializers integrados para a nova experiência do prontuário."""

import json
from pathlib import Path

from django.db import transaction
from rest_framework import serializers

from .extended_models import (
    AnamnesisProfile,
    AnamnesisVersion,
    EvolutionClinicalData,
    EvolutionVersion,
)
from .models import Anamnesis, Evolution
from .treatment_models import ClinicalDocument, TreatmentGoal


ANAMNESIS_LEGACY_FIELDS = (
    "chief_complaint",
    "history",
    "medications",
    "family_history",
    "observations",
)
ANAMNESIS_PROFILE_FIELDS = (
    "reason_for_care",
    "physical_health_history",
    "mental_health_history",
    "previous_treatments",
    "habits_and_routine",
    "sleep",
    "nutrition",
    "family_social_relations",
    "academic_history",
    "professional_history",
    "support_network",
    "relevant_events",
    "initial_assessment",
    "clinical_hypotheses",
    "custom_fields",
)
CLINICAL_DATA_FIELDS = (
    "session_time",
    "duration_minutes",
    "modality",
    "appointment_type",
    "emotional_state",
    "chief_complaint",
    "patient_report",
    "therapist_observations",
    "interventions",
    "perceived_evolution",
    "homework",
    "referrals",
    "next_steps",
)


class ClinicalAnamnesisSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    patient = serializers.IntegerField(read_only=True)
    chief_complaint = serializers.CharField(required=False, allow_blank=True)
    history = serializers.CharField(required=False, allow_blank=True)
    medications = serializers.CharField(required=False, allow_blank=True)
    family_history = serializers.CharField(required=False, allow_blank=True)
    observations = serializers.CharField(required=False, allow_blank=True)
    reason_for_care = serializers.CharField(required=False, allow_blank=True)
    physical_health_history = serializers.CharField(required=False, allow_blank=True)
    mental_health_history = serializers.CharField(required=False, allow_blank=True)
    previous_treatments = serializers.CharField(required=False, allow_blank=True)
    habits_and_routine = serializers.CharField(required=False, allow_blank=True)
    sleep = serializers.CharField(required=False, allow_blank=True)
    nutrition = serializers.CharField(required=False, allow_blank=True)
    family_social_relations = serializers.CharField(required=False, allow_blank=True)
    academic_history = serializers.CharField(required=False, allow_blank=True)
    professional_history = serializers.CharField(required=False, allow_blank=True)
    support_network = serializers.CharField(required=False, allow_blank=True)
    relevant_events = serializers.CharField(required=False, allow_blank=True)
    initial_assessment = serializers.CharField(required=False, allow_blank=True)
    clinical_hypotheses = serializers.CharField(required=False, allow_blank=True)
    custom_fields = serializers.CharField(required=False, allow_blank=True, default="{}")
    completion_percentage = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    version_count = serializers.IntegerField(read_only=True)

    def to_representation(self, instance):
        profile = getattr(instance, "profile", None)
        values = {
            "id": instance.id,
            "patient": instance.patient_id,
            "created_at": instance.created_at,
            "updated_at": max(
                instance.updated_at,
                profile.updated_at if profile else instance.updated_at,
            ),
            "version_count": instance.versions.count(),
        }
        for field in ANAMNESIS_LEGACY_FIELDS:
            values[field] = getattr(instance, field, "") or ""
        for field in ANAMNESIS_PROFILE_FIELDS:
            values[field] = getattr(profile, field, "") if profile else ""

        completed_fields = [
            value
            for key, value in values.items()
            if key in ANAMNESIS_LEGACY_FIELDS + ANAMNESIS_PROFILE_FIELDS
        ]
        values["completion_percentage"] = round(
            (sum(bool(str(value).strip()) for value in completed_fields) / len(completed_fields))
            * 100
        )
        return super().to_representation(values)

    @transaction.atomic
    def save(self, **kwargs):
        patient = self.context["patient"]
        user = self.context["request"].user
        anamnesis, created = Anamnesis.objects.select_for_update().get_or_create(
            patient=patient,
            defaults={
                "chief_complaint": self.validated_data.get("chief_complaint", ""),
                "created_by": user,
            },
        )
        profile, _ = AnamnesisProfile.objects.select_for_update().get_or_create(
            anamnesis=anamnesis,
            defaults={"updated_by": user},
        )

        if not created:
            snapshot = {
                field: getattr(anamnesis, field, "") or ""
                for field in ANAMNESIS_LEGACY_FIELDS
            }
            snapshot.update(
                {
                    field: getattr(profile, field, "") or ""
                    for field in ANAMNESIS_PROFILE_FIELDS
                }
            )
            next_version = (anamnesis.versions.first().version + 1) if anamnesis.versions.exists() else 1
            AnamnesisVersion.objects.create(
                anamnesis=anamnesis,
                version=next_version,
                snapshot=json.dumps(snapshot, ensure_ascii=False),
                created_by=user,
            )

        for field in ANAMNESIS_LEGACY_FIELDS:
            if field in self.validated_data:
                setattr(anamnesis, field, self.validated_data[field])
        if not anamnesis.chief_complaint:
            anamnesis.chief_complaint = "Anamnese em preenchimento"
        anamnesis.save()

        for field in ANAMNESIS_PROFILE_FIELDS:
            if field in self.validated_data:
                setattr(profile, field, self.validated_data[field])
        profile.updated_by = user
        profile.save()
        self.instance = anamnesis
        return anamnesis


class EvolutionWorkspaceSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    is_editable = serializers.SerializerMethodField()
    addenda_count = serializers.IntegerField(source="addenda.count", read_only=True)
    session_time = serializers.TimeField(source="clinical_data.session_time", required=False, allow_null=True)
    duration_minutes = serializers.IntegerField(source="clinical_data.duration_minutes", required=False)
    modality = serializers.ChoiceField(source="clinical_data.modality", choices=EvolutionClinicalData.Modality.choices, required=False)
    appointment_type = serializers.ChoiceField(source="clinical_data.appointment_type", choices=EvolutionClinicalData.AppointmentType.choices, required=False)
    emotional_state = serializers.CharField(source="clinical_data.emotional_state", required=False, allow_blank=True)
    chief_complaint = serializers.CharField(source="clinical_data.chief_complaint", required=False, allow_blank=True)
    patient_report = serializers.CharField(source="clinical_data.patient_report", required=False, allow_blank=True)
    therapist_observations = serializers.CharField(source="clinical_data.therapist_observations", required=False, allow_blank=True)
    interventions = serializers.CharField(source="clinical_data.interventions", required=False, allow_blank=True)
    perceived_evolution = serializers.CharField(source="clinical_data.perceived_evolution", required=False, allow_blank=True)
    homework = serializers.CharField(source="clinical_data.homework", required=False, allow_blank=True)
    referrals = serializers.CharField(source="clinical_data.referrals", required=False, allow_blank=True)
    next_steps = serializers.CharField(source="clinical_data.next_steps", required=False, allow_blank=True)

    class Meta:
        model = Evolution
        fields = (
            "id", "patient", "appointment", "session_date", "session_time",
            "duration_minutes", "modality", "appointment_type", "emotional_state",
            "chief_complaint", "patient_report", "therapist_observations",
            "interventions", "perceived_evolution", "homework", "referrals",
            "next_steps", "content", "cid10", "is_locked", "locked_at",
            "is_editable", "addenda_count", "created_by_name", "created_at",
            "updated_at",
        )
        read_only_fields = (
            "patient", "is_locked", "locked_at", "is_editable", "addenda_count",
            "created_by_name", "created_at", "updated_at",
        )

    def get_is_editable(self, obj):
        return obj.created_by_id == self.context["request"].user.id and obj.can_be_edited()

    def validate_appointment(self, appointment):
        patient = self.context["patient"]
        if appointment and appointment.patient_id != patient.id:
            raise serializers.ValidationError("O agendamento não pertence ao paciente selecionado.")
        if appointment and appointment.therapist_id != patient.therapist_id:
            raise serializers.ValidationError("O agendamento pertence a outro profissional.")
        return appointment

    @transaction.atomic
    def create(self, validated_data):
        clinical_data = validated_data.pop("clinical_data", {})
        patient = self.context["patient"]
        user = self.context["request"].user
        content = validated_data.get("content") or clinical_data.get("therapist_observations") or "Evolução em rascunho"
        evolution = Evolution.objects.create(
            patient=patient,
            created_by=user,
            content=content,
            **validated_data,
        )
        EvolutionClinicalData.objects.create(
            evolution=evolution,
            updated_by=user,
            **clinical_data,
        )
        return evolution

    @transaction.atomic
    def update(self, instance, validated_data):
        if instance.created_by_id != self.context["request"].user.id or not instance.can_be_edited():
            raise serializers.ValidationError("Esta evolução não pode mais ser alterada diretamente.")
        clinical_data = validated_data.pop("clinical_data", {})
        current = {
            "content": instance.content,
            "cid10": instance.cid10,
            "session_date": instance.session_date.isoformat(),
        }
        profile = getattr(instance, "clinical_data", None)
        current.update({field: getattr(profile, field, "") if profile else "" for field in CLINICAL_DATA_FIELDS})
        next_version = (instance.versions.first().version + 1) if instance.versions.exists() else 1
        EvolutionVersion.objects.create(
            evolution=instance,
            version=next_version,
            snapshot=json.dumps(current, ensure_ascii=False, default=str),
            created_by=self.context["request"].user,
        )
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if clinical_data.get("therapist_observations") and not validated_data.get("content"):
            instance.content = clinical_data["therapist_observations"]
        instance.save()
        profile, _ = EvolutionClinicalData.objects.get_or_create(
            evolution=instance,
            defaults={"updated_by": self.context["request"].user},
        )
        for field, value in clinical_data.items():
            setattr(profile, field, value)
        profile.updated_by = self.context["request"].user
        profile.save()
        return instance


class TreatmentGoalSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)

    class Meta:
        model = TreatmentGoal
        fields = (
            "id", "patient", "title", "description", "category", "priority",
            "priority_display", "start_date", "target_date", "status",
            "status_display", "progress", "strategies", "evaluation_criteria",
            "observations", "sort_order", "evolutions", "created_at", "updated_at",
        )
        read_only_fields = ("patient", "created_at", "updated_at")

    def validate_evolutions(self, evolutions):
        patient = self.context["patient"]
        if any(item.patient_id != patient.id for item in evolutions):
            raise serializers.ValidationError("Todas as evoluções devem pertencer ao paciente.")
        return evolutions


class ClinicalDocumentSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    download_url = serializers.SerializerMethodField()
    file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = ClinicalDocument
        fields = (
            "id", "patient", "evolution", "category", "category_display", "file",
            "original_name", "description", "content_type", "size_bytes", "version",
            "is_archived", "created_at", "updated_at", "download_url",
        )
        read_only_fields = (
            "patient", "original_name", "content_type", "size_bytes", "version",
            "is_archived", "created_at", "updated_at", "download_url",
        )

    def get_download_url(self, obj):
        request = self.context.get("request")
        path = f"/api/v1/records/documents/{obj.id}/download/"
        return request.build_absolute_uri(path) if request else path

    def validate_file(self, uploaded_file):
        allowed_types = {
            "application/pdf",
            "image/jpeg",
            "image/png",
            "text/plain",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".txt", ".docx"}
        extension = Path(uploaded_file.name).suffix.lower()
        if uploaded_file.content_type not in allowed_types or extension not in allowed_extensions:
            raise serializers.ValidationError("Tipo de arquivo não permitido.")
        if uploaded_file.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("O arquivo deve possuir no máximo 10 MB.")
        return uploaded_file

    def validate_evolution(self, evolution):
        if evolution and evolution.patient_id != self.context["patient"].id:
            raise serializers.ValidationError("A evolução não pertence ao paciente.")
        return evolution
