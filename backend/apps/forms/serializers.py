from __future__ import annotations

from django.db import transaction
from rest_framework import serializers

from .models import FieldType, FormAnswer, FormField, FormSubmission, FormTemplate, TherapeuticForm

OPTION_FIELDS = {FieldType.SELECT, FieldType.RADIO, FieldType.CHECKBOX}
ALLOWED_FIELD_TYPES = {choice.value for choice in FieldType}


def normalize_options(config: dict) -> list[str]:
    options = config.get("options", [])
    if not isinstance(options, list):
        raise serializers.ValidationError("As opções devem ser uma lista.")
    normalized = [str(item).strip() for item in options if str(item).strip()]
    if not normalized:
        raise serializers.ValidationError("Campos de seleção precisam ter ao menos uma opção.")
    return normalized


def validate_field_payload(field: dict) -> dict:
    field_type = field.get("type")
    if field_type not in ALLOWED_FIELD_TYPES:
        raise serializers.ValidationError({"type": "Tipo de campo inválido."})
    label = str(field.get("label", "")).strip()
    if not label:
        raise serializers.ValidationError({"label": "Informe o nome do campo."})
    config = field.get("config") or {}
    if not isinstance(config, dict):
        raise serializers.ValidationError({"config": "Configuração inválida."})
    if field_type in OPTION_FIELDS:
        config["options"] = normalize_options(config)
    if field_type == FieldType.SCALE:
        min_value = int(config.get("min", 1))
        max_value = int(config.get("max", 10))
        if min_value >= max_value:
            raise serializers.ValidationError({"config": "O valor mínimo da escala deve ser menor que o máximo."})
        config["min"] = min_value
        config["max"] = max_value
        config["step"] = int(config.get("step", 1))
    field["label"] = label[:180]
    field["placeholder"] = str(field.get("placeholder", ""))[:255]
    field["help_text"] = str(field.get("help_text", ""))[:255]
    field["config"] = config
    return field


class FormFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormField
        fields = (
            "id",
            "type",
            "label",
            "placeholder",
            "help_text",
            "required",
            "order",
            "is_visible",
            "internal_id",
            "config",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        return validate_field_payload(attrs)


class FormTemplateSerializer(serializers.ModelSerializer):
    fields_count = serializers.SerializerMethodField()
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = FormTemplate
        fields = (
            "id",
            "name",
            "description",
            "category",
            "category_display",
            "icon",
            "fields_schema",
            "fields_count",
            "is_system_template",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_fields_count(self, obj):
        return len(obj.fields_schema or [])


class TherapeuticFormSerializer(serializers.ModelSerializer):
    fields = FormFieldSerializer(many=True)
    fields_count = serializers.IntegerField(source="fields.count", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    updated_by_name = serializers.CharField(source="updated_by.full_name", read_only=True)

    class Meta:
        model = TherapeuticForm
        fields = (
            "id",
            "name",
            "description",
            "category",
            "category_display",
            "status",
            "status_display",
            "source_template",
            "fields_count",
            "fields",
            "created_by_name",
            "updated_by_name",
            "archived_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "status_display",
            "category_display",
            "source_template",
            "fields_count",
            "created_by_name",
            "updated_by_name",
            "archived_at",
            "created_at",
            "updated_at",
        )

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Informe o nome do formulário.")
        return value

    def validate_fields(self, fields):
        if not fields:
            raise serializers.ValidationError("Adicione ao menos um campo ao formulário.")
        for index, field in enumerate(fields, start=1):
            field["order"] = field.get("order") or index
            validate_field_payload(field)
        return fields

    @transaction.atomic
    def create(self, validated_data):
        fields = validated_data.pop("fields", [])
        user = self.context["request"].user
        form = TherapeuticForm.objects.create(
            owner=user,
            created_by=user,
            updated_by=user,
            **validated_data,
        )
        self._replace_fields(form, fields)
        return form

    @transaction.atomic
    def update(self, instance, validated_data):
        fields = validated_data.pop("fields", None)
        request_user = self.context["request"].user
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.updated_by = request_user
        instance.save()
        if fields is not None:
            self._replace_fields(instance, fields)
        return instance

    def _replace_fields(self, form: TherapeuticForm, fields: list[dict]) -> None:
        form.fields.all().delete()
        FormField.objects.bulk_create(
            [
                FormField(
                    form=form,
                    type=field["type"],
                    label=field["label"],
                    placeholder=field.get("placeholder", ""),
                    help_text=field.get("help_text", ""),
                    required=field.get("required", False),
                    order=field.get("order") or index,
                    is_visible=field.get("is_visible", True),
                    internal_id=field.get("internal_id", ""),
                    config=field.get("config") or {},
                )
                for index, field in enumerate(fields, start=1)
            ]
        )


class FormSubmissionAnswerSerializer(serializers.Serializer):
    field = serializers.IntegerField()
    value = serializers.JSONField(required=False)


class FormAnswerSerializer(serializers.ModelSerializer):
    field_label = serializers.CharField(source="field.label", read_only=True)
    field_type = serializers.CharField(source="field.type", read_only=True)

    class Meta:
        model = FormAnswer
        fields = ("id", "field", "field_label", "field_type", "value", "created_at", "updated_at")
        read_only_fields = ("id", "field_label", "field_type", "created_at", "updated_at")


class FormSubmissionSerializer(serializers.ModelSerializer):
    answers = FormSubmissionAnswerSerializer(many=True, write_only=True, required=False)
    answer_details = FormAnswerSerializer(source="answers", many=True, read_only=True)
    patient_name = serializers.CharField(source="patient.display_name", read_only=True)
    form_name = serializers.CharField(source="form.name", read_only=True)

    class Meta:
        model = FormSubmission
        fields = (
            "id",
            "form",
            "form_name",
            "patient",
            "patient_name",
            "professional",
            "appointment",
            "status",
            "answers",
            "answer_details",
            "submitted_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "form",
            "form_name",
            "patient_name",
            "status",
            "answer_details",
            "submitted_at",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        form = self.context["form"]
        user = self.context["request"].user
        patient = attrs.get("patient")
        if patient and patient.therapist_id != form.owner_id:
            raise serializers.ValidationError({"patient": "Paciente não pertence ao responsável do formulário."})
        appointment = attrs.get("appointment")
        if appointment and appointment.therapist_id != form.owner_id:
            raise serializers.ValidationError({"appointment": "Agendamento não pertence ao responsável do formulário."})
        professional = attrs.get("professional") or user
        attrs["professional"] = professional
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        raw_answers = validated_data.pop("answers", [])
        form = self.context["form"]
        user = self.context["request"].user
        submission = FormSubmission.objects.create(
            form=form,
            owner=form.owner,
            **validated_data,
        )
        self._save_answers(submission, raw_answers)
        return submission

    @transaction.atomic
    def update(self, instance, validated_data):
        raw_answers = validated_data.pop("answers", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if raw_answers is not None:
            instance.answers.all().delete()
            self._save_answers(instance, raw_answers)
        return instance

    def _save_answers(self, submission, raw_answers):
        fields = {field.id: field for field in submission.form.fields.all()}
        answers = []
        for answer in raw_answers:
            field = fields.get(answer["field"])
            if not field:
                raise serializers.ValidationError({"answers": "Campo inválido para este formulário."})
            answers.append(FormAnswer(submission=submission, field=field, value=answer.get("value")))
        FormAnswer.objects.bulk_create(answers)
