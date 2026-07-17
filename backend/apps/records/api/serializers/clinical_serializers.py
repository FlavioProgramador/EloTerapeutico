"""Serializers integrados para a experiência do prontuário eletrônico."""

import json
from pathlib import Path

from django.db import transaction
from rest_framework import serializers

from apps.records.extended_models import (
    AnamnesisProfile,
    AnamnesisVersion,
    EvolutionClinicalData,
    EvolutionVersion,
)
from apps.records.models import Anamnesis, Evolution
from apps.records.treatment_models import (
    ClinicalDocument,
    ClinicalExport,
    ClinicalFormResponse,
    TreatmentGoal,
)

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
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    updated_by_name = serializers.CharField(read_only=True)
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
            "updated_by_name": (profile.updated_by.full_name if profile and profile.updated_by else ""),
            "version_count": instance.versions.count(),
        }
        for field in ANAMNESIS_LEGACY_FIELDS:
            values[field] = getattr(instance, field, "") or ""
        for field in ANAMNESIS_PROFILE_FIELDS:
            values[field] = getattr(profile, field, "") if profile else ""

        completed_fields = [
            value for key, value in values.items() if key in ANAMNESIS_LEGACY_FIELDS + ANAMNESIS_PROFILE_FIELDS
        ]
        completion_percentage = round(
            sum(bool(str(value).strip()) for value in completed_fields) / len(completed_fields) * 100
        )
        values["completion_percentage"] = completion_percentage
        values["status"] = "complete" if completion_percentage == 100 else "draft"
        values["status_display"] = "Completa" if completion_percentage == 100 else "Rascunho"
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
            snapshot = {field: getattr(anamnesis, field, "") or "" for field in ANAMNESIS_LEGACY_FIELDS}
            snapshot.update({field: getattr(profile, field, "") or "" for field in ANAMNESIS_PROFILE_FIELDS})
            latest = anamnesis.versions.first()
            AnamnesisVersion.objects.create(
                anamnesis=anamnesis,
                version=(latest.version + 1) if latest else 1,
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
    content = serializers.CharField(required=False, allow_blank=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    is_editable = serializers.SerializerMethodField()
    addenda_count = serializers.IntegerField(read_only=True)
    attached_documents_count = serializers.IntegerField(read_only=True)
    linked_goal_ids = serializers.PrimaryKeyRelatedField(
        source="treatment_goals",
        many=True,
        read_only=True,
    )
    session_time = serializers.TimeField(
        source="clinical_data.session_time",
        required=False,
        allow_null=True,
    )
    duration_minutes = serializers.IntegerField(
        source="clinical_data.duration_minutes",
        required=False,
    )
    modality = serializers.ChoiceField(
        source="clinical_data.modality",
        choices=EvolutionClinicalData.Modality.choices,
        required=False,
    )
    appointment_type = serializers.ChoiceField(
        source="clinical_data.appointment_type",
        choices=EvolutionClinicalData.AppointmentType.choices,
        required=False,
    )
    emotional_state = serializers.CharField(
        source="clinical_data.emotional_state",
        required=False,
        allow_blank=True,
    )
    chief_complaint = serializers.CharField(
        source="clinical_data.chief_complaint",
        required=False,
        allow_blank=True,
    )
    patient_report = serializers.CharField(
        source="clinical_data.patient_report",
        required=False,
        allow_blank=True,
    )
    therapist_observations = serializers.CharField(
        source="clinical_data.therapist_observations",
        required=False,
        allow_blank=True,
    )
    interventions = serializers.CharField(
        source="clinical_data.interventions",
        required=False,
        allow_blank=True,
    )
    perceived_evolution = serializers.CharField(
        source="clinical_data.perceived_evolution",
        required=False,
        allow_blank=True,
    )
    homework = serializers.CharField(
        source="clinical_data.homework",
        required=False,
        allow_blank=True,
    )
    referrals = serializers.CharField(
        source="clinical_data.referrals",
        required=False,
        allow_blank=True,
    )
    next_steps = serializers.CharField(
        source="clinical_data.next_steps",
        required=False,
        allow_blank=True,
    )

    class Meta:
        model = Evolution
        fields = (
            "id",
            "patient",
            "appointment",
            "session_date",
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
            "content",
            "cid10",
            "is_locked",
            "locked_at",
            "is_editable",
            "is_confidential",
            "addenda_count",
            "attached_documents_count",
            "linked_goal_ids",
            "created_by_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "patient",
            "is_locked",
            "locked_at",
            "is_editable",
            "addenda_count",
            "attached_documents_count",
            "linked_goal_ids",
            "created_by_name",
            "created_at",
            "updated_at",
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
        supplied_content = validated_data.pop("content", "")
        content = supplied_content or clinical_data.get("therapist_observations") or "Evolução em rascunho"
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
        request_user = self.context["request"].user
        if instance.created_by_id != request_user.id or not instance.can_be_edited():
            raise serializers.ValidationError("Esta evolução não pode mais ser alterada diretamente.")

        clinical_data = validated_data.pop("clinical_data", {})
        current = {
            "content": instance.content,
            "cid10": instance.cid10,
            "session_date": instance.session_date.isoformat(),
            "is_confidential": instance.is_confidential,
        }
        profile = getattr(instance, "clinical_data", None)
        current.update({field: getattr(profile, field, "") if profile else "" for field in CLINICAL_DATA_FIELDS})
        latest = instance.versions.first()
        EvolutionVersion.objects.create(
            evolution=instance,
            version=(latest.version + 1) if latest else 1,
            snapshot=json.dumps(current, ensure_ascii=False, default=str),
            created_by=request_user,
        )

        for field, value in validated_data.items():
            setattr(instance, field, value)
        if clinical_data.get("therapist_observations") and "content" not in validated_data:
            instance.content = clinical_data["therapist_observations"]
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


class TreatmentGoalSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(
        source="get_priority_display",
        read_only=True,
    )
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = TreatmentGoal
        fields = (
            "id",
            "patient",
            "title",
            "description",
            "category",
            "priority",
            "priority_display",
            "start_date",
            "target_date",
            "status",
            "status_display",
            "progress",
            "strategies",
            "evaluation_criteria",
            "observations",
            "sort_order",
            "evolutions",
            "created_by_name",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "patient",
            "created_by_name",
            "created_at",
            "updated_at",
        )

    def validate_evolutions(self, evolutions):
        patient = self.context["patient"]
        user = self.context["request"].user

        for item in evolutions:
            if item.patient_id != patient.id:
                raise serializers.ValidationError("Todas as evoluções devem pertencer ao paciente.")

            # Validação de confidencialidade ao vincular
            if item.is_confidential:
                if (
                    item.created_by_id != user.id
                    and not user.has_perm("records.view_confidential_evolution")
                ):
                    raise serializers.ValidationError(
                        f"Você não pode vincular a evolução #{item.id} pois ela é confidencial e pertence a outro autor."
                    )

        return evolutions

    def to_representation(self, instance):
        """Filtra evoluções confidenciais da resposta caso o usuário não tenha acesso."""
        data = super().to_representation(instance)
        request = self.context.get("request")

        if not request or not data.get("evolutions"):
            return data

        user = request.user
        if user.has_perm("records.view_confidential_evolution"):
            return data

        # Se o usuário não tem permissão global, filtramos as evoluções
        # que ele não criou e que são confidenciais.
        # Infelizmente, 'evolutions' no data são apenas IDs.
        # Precisamos verificar a confidencialidade de cada uma.
        authorized_evolution_ids = []
        for evol in instance.evolutions.all():
            if not evol.is_confidential or evol.created_by_id == user.id:
                authorized_evolution_ids.append(evol.id)

        data["evolutions"] = authorized_evolution_ids
        return data


class ClinicalDocumentSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(
        source="get_category_display",
        read_only=True,
    )
    uploaded_by_name = serializers.CharField(
        source="uploaded_by.full_name",
        read_only=True,
    )
    evolution_date = serializers.DateField(
        source="evolution.session_date",
        read_only=True,
        allow_null=True,
    )
    status = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = ClinicalDocument
        fields = (
            "id",
            "patient",
            "evolution",
            "evolution_date",
            "category",
            "category_display",
            "file",
            "original_name",
            "description",
            "content_type",
            "size_bytes",
            "version",
            "is_archived",
            "status",
            "status_display",
            "uploaded_by_name",
            "created_at",
            "updated_at",
            "download_url",
        )
        read_only_fields = (
            "patient",
            "evolution_date",
            "original_name",
            "content_type",
            "size_bytes",
            "version",
            "is_archived",
            "status",
            "status_display",
            "uploaded_by_name",
            "created_at",
            "updated_at",
            "download_url",
        )

    def get_status(self, obj):
        return "archived" if obj.is_archived else "available"

    def get_status_display(self, obj):
        return "Arquivado" if obj.is_archived else "Disponível"

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
        if not evolution:
            return evolution

        patient = self.context["patient"]
        if evolution.patient_id != patient.id:
            raise serializers.ValidationError("A evolução não pertence ao paciente.")

        # Validação de confidencialidade ao vincular
        user = self.context["request"].user
        if evolution.is_confidential:
            if (
                evolution.created_by_id != user.id
                and not user.has_perm("records.view_confidential_evolution")
            ):
                raise serializers.ValidationError(
                    "Você não pode vincular documentos a uma evolução confidencial de outro autor."
                )

        return evolution


class ClinicalFormResponseSerializer(serializers.ModelSerializer):
    therapist_name = serializers.CharField(source="therapist.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ClinicalFormResponse
        fields = (
            "id",
            "patient",
            "form_name",
            "category",
            "sent_at",
            "completed_at",
            "completed_by",
            "therapist",
            "therapist_name",
            "status",
            "status_display",
            "answers_count",
            "form_snapshot",
            "answers",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "patient",
            "therapist",
            "therapist_name",
            "status_display",
            "created_at",
            "updated_at",
        )


class ClinicalExportSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ClinicalExport
        fields = (
            "id",
            "patient",
            "export_type",
            "filename",
            "period",
            "status",
            "status_display",
            "size_bytes",
            "download_url",
            "started_at",
            "completed_at",
            "created_by",
            "created_by_name",
            "created_at",
            "retries",
            "error_message",
        )
        read_only_fields = (
            "patient",
            "filename",
            "status_display",
            "size_bytes",
            "download_url",
            "started_at",
            "completed_at",
            "created_by",
            "created_by_name",
            "created_at",
            "retries",
            "error_message",
        )
