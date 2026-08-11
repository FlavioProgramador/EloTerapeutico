from rest_framework import serializers

from apps.forms.exceptions import FinalizedSubmissionError, InvalidFormAnswerError
from apps.forms.models import FormAnswer, FormSubmission
from apps.forms.services import create_submission, update_submission
from apps.organizations.models import OrganizationMembership
from apps.patients.models import Patient
from apps.scheduling.models import Appointment
from apps.users.models import User


class FormSubmissionAnswerSerializer(serializers.Serializer):
    field = serializers.IntegerField()
    value = serializers.JSONField(required=False)


class FormAnswerSerializer(serializers.ModelSerializer):
    field_label = serializers.CharField(source="field.label", read_only=True)
    field_type = serializers.CharField(source="field.type", read_only=True)

    class Meta:
        model = FormAnswer
        fields = (
            "id",
            "field",
            "field_label",
            "field_type",
            "value",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "field_label",
            "field_type",
            "created_at",
            "updated_at",
        )


class FormSubmissionSerializer(serializers.ModelSerializer):
    answers = FormSubmissionAnswerSerializer(
        many=True,
        write_only=True,
        required=False,
    )
    answer_details = FormAnswerSerializer(
        source="answers",
        many=True,
        read_only=True,
    )
    patient_name = serializers.CharField(
        source="patient.display_name",
        read_only=True,
    )
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        form = self.context.get("form")
        organization = getattr(request, "organization", None) or getattr(
            form,
            "organization",
            None,
        )
        self.fields["patient"].queryset = (
            Patient.objects.filter(organization=organization, is_active=True)
            if organization is not None
            else Patient.objects.none()
        )
        self.fields["appointment"].queryset = (
            Appointment.objects.filter(organization=organization)
            if organization is not None
            else Appointment.objects.none()
        )
        member_ids = (
            OrganizationMembership.objects.filter(
                organization=organization,
                status=OrganizationMembership.Status.ACTIVE,
                role__in=[
                    OrganizationMembership.Role.OWNER,
                    OrganizationMembership.Role.ADMIN,
                    OrganizationMembership.Role.THERAPIST,
                ],
            ).values_list("user_id", flat=True)
            if organization is not None
            else []
        )
        self.fields["professional"].queryset = User.objects.filter(pk__in=member_ids)

    def validate(self, attrs):
        form = self.context["form"]
        request = self.context["request"]
        organization = getattr(request, "organization", None)
        if organization is None or form.organization_id != organization.pk:
            raise serializers.ValidationError(
                {"form": "O formulário pertence a outra organização."}
            )
        patient = attrs.get("patient", getattr(self.instance, "patient", None))
        if patient and patient.organization_id != organization.pk:
            raise serializers.ValidationError(
                {"patient": "Paciente pertence a outra organização."}
            )
        appointment = attrs.get(
            "appointment",
            getattr(self.instance, "appointment", None),
        )
        if appointment:
            if appointment.organization_id != organization.pk:
                raise serializers.ValidationError(
                    {"appointment": "Agendamento pertence a outra organização."}
                )
            if patient and appointment.patient_id != patient.pk:
                raise serializers.ValidationError(
                    {"appointment": "Agendamento pertence a outro paciente."}
                )
        professional = attrs.get("professional") or request.user
        if not OrganizationMembership.objects.filter(
            organization=organization,
            user=professional,
            status=OrganizationMembership.Status.ACTIVE,
        ).exists():
            raise serializers.ValidationError(
                {"professional": "Profissional não autorizado nesta organização."}
            )
        attrs["professional"] = professional
        return attrs

    def create(self, validated_data):
        try:
            return create_submission(
                actor=self.context["request"].user,
                form=self.context["form"],
                validated_data=validated_data,
            )
        except InvalidFormAnswerError as exc:
            raise serializers.ValidationError({"answers": str(exc)}) from exc

    def update(self, instance, validated_data):
        try:
            return update_submission(
                actor=self.context["request"].user,
                submission=instance,
                validated_data=validated_data,
            )
        except InvalidFormAnswerError as exc:
            raise serializers.ValidationError({"answers": str(exc)}) from exc
        except FinalizedSubmissionError as exc:
            raise serializers.ValidationError(str(exc)) from exc
