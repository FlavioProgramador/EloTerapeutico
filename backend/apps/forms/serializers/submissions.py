from rest_framework import serializers

from apps.forms.exceptions import FinalizedSubmissionError, InvalidFormAnswerError
from apps.forms.models import FormAnswer, FormSubmission
from apps.forms.services import create_submission, update_submission


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
        if professional.id != form.owner_id and not user.is_admin_role:
            raise serializers.ValidationError({"professional": "Profissional não autorizado para este formulário."})
        attrs["professional"] = professional
        return attrs

    def create(self, validated_data):
        try:
            return create_submission(
                form=self.context["form"],
                validated_data=validated_data,
            )
        except InvalidFormAnswerError as exc:
            raise serializers.ValidationError({"answers": str(exc)}) from exc

    def update(self, instance, validated_data):
        try:
            return update_submission(
                submission=instance,
                validated_data=validated_data,
            )
        except InvalidFormAnswerError as exc:
            raise serializers.ValidationError({"answers": str(exc)}) from exc
        except FinalizedSubmissionError as exc:
            raise serializers.ValidationError(str(exc)) from exc
