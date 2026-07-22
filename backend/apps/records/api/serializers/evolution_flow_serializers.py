"""Serializers do fluxo seguro e compacto de evolução clínica."""

from __future__ import annotations

import json

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.records.extended_models import EvolutionClinicalData, EvolutionVersion
from apps.records.models import Evolution
from apps.records.models.templates import ClinicalEvolutionTemplate
from apps.records.services.evolution_security import (
    sanitize_clinical_markdown,
    sanitize_original_filename,
    validate_clinical_upload,
    validate_session_date,
)
from apps.records.treatment_models import ClinicalDocument
from apps.scheduling.models import Appointment

CLINICAL_TEXT_FIELDS = (
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


class EvolutionAppointmentOptionSerializer(serializers.ModelSerializer):
    therapist_name = serializers.CharField(source="therapist.full_name", read_only=True)
    patient_name = serializers.CharField(source="patient.display_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    modality_display = serializers.CharField(source="get_modality_display", read_only=True)
    type_display = serializers.CharField(source="get_appointment_type_display", read_only=True)

    class Meta:
        model = Appointment
        fields = (
            "id",
            "patient",
            "patient_name",
            "therapist",
            "therapist_name",
            "start_time",
            "end_time",
            "status",
            "status_display",
            "modality",
            "modality_display",
            "appointment_type",
            "type_display",
        )
        read_only_fields = fields


class EvolutionAttachmentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True, required=True)
    download_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()

    class Meta:
        model = ClinicalDocument
        fields = (
            "id",
            "file",
            "original_name",
            "content_type",
            "size_bytes",
            "created_at",
            "download_url",
            "preview_url",
        )
        read_only_fields = (
            "id",
            "original_name",
            "content_type",
            "size_bytes",
            "created_at",
            "download_url",
            "preview_url",
        )

    def validate_file(self, value):
        return validate_clinical_upload(value)

    def get_download_url(self, obj):
        request = self.context.get("request")
        path = f"/api/v1/records/clinical-evolutions/{obj.evolution_id}/attachments/{obj.id}/download/"
        return request.build_absolute_uri(path) if request else path

    def get_preview_url(self, obj):
        if not obj.content_type.startswith("image/"):
            return None
        return self.get_download_url(obj)

    @transaction.atomic
    def create(self, validated_data):
        uploaded_file = validated_data.pop("file")
        evolution = self.context["evolution"]
        request = self.context["request"]
        return ClinicalDocument.objects.create(
            organization=evolution.patient.organization,
            patient=evolution.patient,
            evolution=evolution,
            category=ClinicalDocument.Category.OTHER,
            file=uploaded_file,
            original_name=sanitize_original_filename(uploaded_file.name),
            description="Anexo protegido da evolução clínica",
            content_type=uploaded_file.content_type,
            size_bytes=uploaded_file.size,
            checksum=ClinicalDocument.calculate_checksum(uploaded_file),
            uploaded_by=request.user,
        )


class ClinicalEvolutionTemplateSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source="owner.full_name", read_only=True)
    is_system = serializers.SerializerMethodField()

    class Meta:
        model = ClinicalEvolutionTemplate
        fields = (
            "id",
            "name",
            "content",
            "owner",
            "owner_name",
            "is_system",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "owner",
            "owner_name",
            "is_system",
            "created_at",
            "updated_at",
        )

    def get_is_system(self, obj):
        return obj.owner_id is None

    def validate_name(self, value):
        value = " ".join(value.split()).strip()
        if len(value) < 2:
            raise serializers.ValidationError("Informe um nome para o template.")
        return value

    def validate_content(self, value):
        value = sanitize_clinical_markdown(value)
        if not value:
            raise serializers.ValidationError("O template não pode estar vazio.")
        return value


class EvolutionFlowSerializer(serializers.ModelSerializer):
    appointment = serializers.PrimaryKeyRelatedField(
        queryset=Appointment.objects.select_related("patient", "therapist").all(),
        required=False,
        allow_null=True,
    )
    content = serializers.CharField(required=False, allow_blank=True)
    content_format = serializers.ChoiceField(
        choices=("markdown", "plain_text"),
        default="markdown",
        required=False,
    )
    confirm_appointment_date_override = serializers.BooleanField(
        write_only=True,
        required=False,
        default=False,
    )
    session_time = serializers.TimeField(source="clinical_data.session_time", required=False, allow_null=True)
    duration_minutes = serializers.IntegerField(
        source="clinical_data.duration_minutes",
        required=False,
        min_value=1,
        max_value=600,
        default=50,
    )
    modality = serializers.ChoiceField(
        source="clinical_data.modality",
        choices=EvolutionClinicalData.Modality.choices,
        required=False,
        default=EvolutionClinicalData.Modality.IN_PERSON,
    )
    appointment_type = serializers.ChoiceField(
        source="clinical_data.appointment_type",
        choices=EvolutionClinicalData.AppointmentType.choices,
        required=False,
        default=EvolutionClinicalData.AppointmentType.INDIVIDUAL,
    )
    emotional_state = serializers.CharField(source="clinical_data.emotional_state", required=False, allow_blank=True)
    chief_complaint = serializers.CharField(source="clinical_data.chief_complaint", required=False, allow_blank=True)
    patient_report = serializers.CharField(source="clinical_data.patient_report", required=False, allow_blank=True)
    therapist_observations = serializers.CharField(
        source="clinical_data.therapist_observations",
        required=False,
        allow_blank=True,
    )
    interventions = serializers.CharField(source="clinical_data.interventions", required=False, allow_blank=True)
    perceived_evolution = serializers.CharField(
        source="clinical_data.perceived_evolution", required=False, allow_blank=True
    )
    homework = serializers.CharField(source="clinical_data.homework", required=False, allow_blank=True)
    referrals = serializers.CharField(source="clinical_data.referrals", required=False, allow_blank=True)
    next_steps = serializers.CharField(source="clinical_data.next_steps", required=False, allow_blank=True)
    status = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    is_editable = serializers.SerializerMethodField()
    version_count = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    appointment_data = serializers.SerializerMethodField()

    class Meta:
        model = Evolution
        fields = (
            "id",
            "patient",
            "appointment",
            "appointment_data",
            "session_date",
            "session_time",
            "duration_minutes",
            "modality",
            "appointment_type",
            "content",
            "content_format",
            "emotional_state",
            "chief_complaint",
            "patient_report",
            "therapist_observations",
            "interventions",
            "perceived_evolution",
            "homework",
            "referrals",
            "next_steps",
            "cid10",
            "is_confidential",
            "is_locked",
            "locked_at",
            "is_editable",
            "status",
            "status_display",
            "version_count",
            "attachments",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
            "confirm_appointment_date_override",
        )
        read_only_fields = (
            "id",
            "patient",
            "appointment_data",
            "is_locked",
            "locked_at",
            "is_editable",
            "status",
            "status_display",
            "version_count",
            "attachments",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        )

    def get_status(self, obj):
        profile = getattr(obj, "clinical_data", None)
        return profile.status if profile else EvolutionClinicalData.Status.DRAFT

    def get_status_display(self, obj):
        profile = getattr(obj, "clinical_data", None)
        return profile.get_status_display() if profile else "Rascunho"

    def get_is_editable(self, obj):
        request = self.context.get("request")
        return bool(
            request
            and obj.created_by_id == request.user.id
            and obj.can_be_edited()
            and self.get_status(obj) == EvolutionClinicalData.Status.DRAFT
        )

    def get_version_count(self, obj):
        count = getattr(obj, "annotated_versions_count", None)
        if count is not None:
            return count

        prefetched = getattr(obj, "_prefetched_objects_cache", {})
        if "versions" in prefetched:
            return len(prefetched["versions"])
        return obj.versions.count()

    def get_attachments(self, obj):
        active_docs = getattr(obj, "active_documents", None)
        if active_docs is not None:
            return EvolutionAttachmentSerializer(
                active_docs,
                many=True,
                context=self.context,
            ).data

        queryset = obj.documents.filter(
            deleted_at__isnull=True,
            is_archived=False,
        ).order_by("created_at")
        return EvolutionAttachmentSerializer(
            queryset,
            many=True,
            context=self.context,
        ).data

    def get_appointment_data(self, obj):
        if not obj.appointment_id:
            return None
        return EvolutionAppointmentOptionSerializer(obj.appointment).data

    def validate_session_date(self, value):
        request = self.context["request"]
        try:
            return validate_session_date(value, request.user)
        except Exception as exc:
            message = getattr(exc, "messages", [str(exc)])[0]
            raise serializers.ValidationError(message) from exc

    def validate_appointment(self, appointment):
        if appointment is None:
            return appointment
        patient = self.context["patient"]
        request = self.context["request"]
        if appointment.patient_id != patient.id:
            raise serializers.ValidationError("A consulta não pertence ao paciente selecionado.")
        if appointment.status == Appointment.Status.CANCELLED:
            raise serializers.ValidationError("Consultas canceladas não podem ser vinculadas a uma evolução.")
        if (
            appointment.therapist_id != request.user.id
            and not request.user.is_admin_role
            and appointment.therapist_id != patient.therapist_id
        ):
            raise serializers.ValidationError("A consulta pertence a um profissional não autorizado.")
        linked = Evolution.objects.filter(appointment=appointment)
        if self.instance:
            linked = linked.exclude(pk=self.instance.pk)
        if linked.exists():
            raise serializers.ValidationError("Esta consulta já está vinculada a outra evolução.")
        return appointment

    def validate(self, attrs):
        clinical_data = attrs.get("clinical_data", {})
        supplied_content = attrs.get("content")
        observation = clinical_data.get("therapist_observations")
        content = sanitize_clinical_markdown(supplied_content or observation)
        if not content:
            raise serializers.ValidationError({"content": "Informe a evolução ou as anotações clínicas."})
        attrs["content"] = content
        clinical_data["therapist_observations"] = sanitize_clinical_markdown(observation or content)
        for field in CLINICAL_TEXT_FIELDS:
            if field in clinical_data:
                clinical_data[field] = sanitize_clinical_markdown(clinical_data[field])
        attrs["clinical_data"] = clinical_data

        appointment = attrs.get("appointment", getattr(self.instance, "appointment", None))
        session_date = attrs.get("session_date", getattr(self.instance, "session_date", None))
        confirm_override = attrs.get("confirm_appointment_date_override", False)
        if appointment and session_date:
            appointment_date = timezone.localtime(appointment.start_time).date()
            if appointment_date != session_date and not confirm_override:
                raise serializers.ValidationError(
                    {
                        "session_date": (
                            "A data difere da consulta vinculada. Confirme a alteração " "manual antes de salvar."
                        )
                    }
                )
        return attrs

    @staticmethod
    def _snapshot(instance):
        profile = getattr(instance, "clinical_data", None)
        snapshot = {
            "appointment_id": instance.appointment_id,
            "session_date": instance.session_date.isoformat(),
            "content": instance.content,
            "cid10": instance.cid10,
            "is_confidential": instance.is_confidential,
        }
        for field in (
            "session_time",
            "duration_minutes",
            "modality",
            "appointment_type",
            *CLINICAL_TEXT_FIELDS,
        ):
            snapshot[field] = getattr(profile, field, "") if profile else ""
        return snapshot

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("content_format", None)
        validated_data.pop("confirm_appointment_date_override", None)
        clinical_data = validated_data.pop("clinical_data", {})
        patient = self.context["patient"]
        user = self.context["request"].user
        evolution = Evolution.objects.create(
            organization=patient.organization,
            patient=patient,
            created_by=user,
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
        request_user = self.context["request"].user
        profile = getattr(instance, "clinical_data", None)
        if (
            instance.created_by_id != request_user.id
            or not instance.can_be_edited()
            or (profile and profile.status != EvolutionClinicalData.Status.DRAFT)
        ):
            raise serializers.ValidationError("Esta evolução não pode mais ser alterada diretamente.")

        validated_data.pop("content_format", None)
        validated_data.pop("confirm_appointment_date_override", None)
        clinical_data = validated_data.pop("clinical_data", {})
        latest = instance.versions.order_by("-version").first()
        EvolutionVersion.objects.create(
            evolution=instance,
            version=(latest.version + 1) if latest else 1,
            snapshot=json.dumps(self._snapshot(instance), ensure_ascii=False, default=str),
            created_by=request_user,
        )

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        profile, _ = EvolutionClinicalData.objects.get_or_create(
            evolution=instance,
            defaults={"updated_by": request_user},
        )
        for field, value in clinical_data.items():
            setattr(profile, field, value)
        profile.updated_by = request_user
        profile.save()
        return instance
