from __future__ import annotations

import uuid

from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from apps.agenda.models import Appointment
from apps.patients.models import Patient

from .models import (
    Communication,
    CommunicationAttempt,
    CommunicationAutomation,
    CommunicationAutomationRun,
    CommunicationChannelConfig,
    CommunicationPreference,
    CommunicationRecipient,
    CommunicationTemplate,
    InAppNotification,
)
from .services import create_communication
from .validators import plain_text_to_safe_html, validate_template_text


class CommunicationRecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationRecipient
        fields = ["id", "recipient_type", "name", "destination_masked", "channel", "status", "blocked_reason"]
        read_only_fields = fields


class CommunicationAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationAttempt
        fields = ["id", "attempt_number", "provider", "status", "external_id", "response_code", "error_code", "error_message", "started_at", "finished_at", "next_retry_at", "latency_ms", "created_at"]
        read_only_fields = fields


class CommunicationListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    recipient = serializers.SerializerMethodField()

    class Meta:
        model = Communication
        fields = ["public_id", "patient", "patient_name", "category", "channel", "subject", "status", "priority", "scheduled_at", "sent_at", "created_at", "created_by_name", "recipient", "source_event"]

    def get_recipient(self, obj):
        recipient = next(iter(obj.recipients.all()), None)
        return recipient.destination_masked if recipient else ""


class CommunicationDetailSerializer(serializers.ModelSerializer):
    recipients = CommunicationRecipientSerializer(many=True, read_only=True)
    attempts = CommunicationAttemptSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    template_name = serializers.CharField(source="template.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = Communication
        fields = ["public_id", "patient", "patient_name", "appointment", "form_submission", "document", "financial_transaction", "direction", "channel", "category", "status", "priority", "subject", "body", "body_html", "template", "template_name", "scheduled_at", "queued_at", "processing_started_at", "sent_at", "delivered_at", "read_at", "responded_at", "failed_at", "canceled_at", "expires_at", "source_event", "source_object_type", "source_object_id", "provider_name", "created_at", "updated_at", "created_by_name", "recipients", "attempts", "metadata"]
        read_only_fields = fields


class CommunicationCreateSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(required=False, allow_null=True)
    appointment_id = serializers.IntegerField(required=False, allow_null=True)
    channel = serializers.ChoiceField(choices=Communication.Channel.choices)
    category = serializers.ChoiceField(choices=Communication.Category.choices, default=Communication.Category.OTHER)
    template_id = serializers.IntegerField(required=False, allow_null=True)
    subject = serializers.CharField(required=False, allow_blank=True, max_length=255)
    body = serializers.CharField(required=False, allow_blank=True, max_length=10000)
    variables = serializers.JSONField(required=False, default=dict)
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)
    priority = serializers.ChoiceField(choices=Communication.Priority.choices, default=Communication.Priority.NORMAL)
    recipient_type = serializers.ChoiceField(choices=CommunicationRecipient.RecipientType.choices, required=False, allow_null=True)
    draft = serializers.BooleanField(default=False)

    def validate(self, attrs):
        request = self.context["request"]
        patient_id = attrs.get("patient_id")
        appointment_id = attrs.get("appointment_id")
        patient = None
        appointment = None
        if patient_id:
            patient = Patient.objects.filter(pk=patient_id, therapist=request.user).first()
            if patient is None:
                raise serializers.ValidationError({"patient_id": "Paciente não encontrado."})
        if appointment_id:
            appointment = Appointment.objects.filter(pk=appointment_id, therapist=request.user).first()
            if appointment is None:
                raise serializers.ValidationError({"appointment_id": "Consulta não encontrada."})
            patient = patient or appointment.patient
        if attrs["channel"] != Communication.Channel.IN_APP and patient is None:
            raise serializers.ValidationError({"patient_id": "Selecione um paciente para este canal."})
        template = None
        template_id = attrs.get("template_id")
        if template_id:
            template = CommunicationTemplate.objects.filter(
                Q(owner=request.user) | Q(owner__isnull=True, is_system_template=True),
                pk=template_id,
                is_active=True,
                is_archived=False,
            ).first()
            if template is None:
                raise serializers.ValidationError({"template_id": "Template não encontrado."})
            if template.channel != attrs["channel"]:
                raise serializers.ValidationError({"template_id": "O template não pertence ao canal selecionado."})
        elif not attrs.get("body", "").strip():
            raise serializers.ValidationError({"body": "Informe o conteúdo ou selecione um template."})
        attrs["patient"] = patient
        attrs["appointment"] = appointment
        attrs["template"] = template
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        validated_data.pop("patient_id", None)
        validated_data.pop("appointment_id", None)
        validated_data.pop("template_id", None)
        idempotency_key = request.headers.get("Idempotency-Key") or f"manual:{request.user.pk}:{uuid.uuid4().hex}"
        return create_communication(owner=request.user, created_by=request.user, idempotency_key=idempotency_key, source_event="manual", **validated_data)


class CommunicationDraftUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Communication
        fields = ["subject", "body", "category", "priority", "scheduled_at"]

    def validate(self, attrs):
        if self.instance.status != Communication.Status.DRAFT:
            raise serializers.ValidationError("Somente rascunhos podem ser editados.")
        body = attrs.get("body", self.instance.body)
        if not str(body).strip():
            raise serializers.ValidationError({"body": "O conteúdo é obrigatório."})
        scheduled_at = attrs.get("scheduled_at")
        if scheduled_at and scheduled_at <= timezone.now():
            raise serializers.ValidationError({"scheduled_at": "A data deve estar no futuro."})
        return attrs

    def update(self, instance, validated_data):
        if "body" in validated_data:
            instance.body_html = plain_text_to_safe_html(validated_data["body"])
        return super().update(instance, validated_data)


class CommunicationTemplateSerializer(serializers.ModelSerializer):
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = CommunicationTemplate
        fields = ["id", "name", "slug", "description", "category", "channel", "subject_template", "body_template", "allowed_variables", "is_system_template", "is_active", "is_archived", "can_edit", "created_at", "updated_at"]
        read_only_fields = ["allowed_variables", "is_system_template", "created_at", "updated_at"]

    def get_can_edit(self, obj):
        request = self.context.get("request")
        return bool(request and obj.owner_id == request.user.pk and not obj.is_system_template)

    def validate(self, attrs):
        subject = attrs.get("subject_template", getattr(self.instance, "subject_template", ""))
        body = attrs.get("body_template", getattr(self.instance, "body_template", ""))
        attrs["allowed_variables"] = validate_template_text(subject, body)
        if self.instance and self.instance.is_system_template:
            raise serializers.ValidationError("Templates do sistema não podem ser editados.")
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return CommunicationTemplate.objects.create(owner=request.user, created_by=request.user, updated_by=request.user, **validated_data)

    def update(self, instance, validated_data):
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


class CommunicationAutomationSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True)
    last_run_at = serializers.SerializerMethodField()
    failures = serializers.SerializerMethodField()

    class Meta:
        model = CommunicationAutomation
        fields = ["id", "name", "description", "event_type", "channel", "template", "template_name", "is_active", "delay_value", "delay_unit", "send_before_event", "conditions", "allowed_start_time", "allowed_end_time", "allowed_weekdays", "respect_preferences", "max_executions", "priority", "fallback_channel", "last_run_at", "failures", "created_at", "updated_at"]
        read_only_fields = ["is_active", "created_at", "updated_at"]

    def get_last_run_at(self, obj):
        run = obj.runs.order_by("-started_at").first()
        return run.started_at if run else None

    def get_failures(self, obj):
        return obj.runs.filter(status=CommunicationAutomationRun.Status.FAILED).count()

    def validate_template(self, template):
        request = self.context["request"]
        if template.owner_id not in {None, request.user.pk}:
            raise serializers.ValidationError("Template inválido.")
        return template

    def validate(self, attrs):
        template = attrs.get("template", getattr(self.instance, "template", None))
        channel = attrs.get("channel", getattr(self.instance, "channel", None))
        if template and channel and template.channel != channel:
            raise serializers.ValidationError({"template": "O template deve usar o mesmo canal da automação."})
        allowed_operators = {"equals", "not_equals", "contains", "greater_than", "less_than", "is_empty", "is_not_empty"}
        for condition in attrs.get("conditions", []):
            if not isinstance(condition, dict) or condition.get("operator") not in allowed_operators:
                raise serializers.ValidationError({"conditions": "A lista contém uma condição inválida."})
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        return CommunicationAutomation.objects.create(owner=request.user, created_by=request.user, updated_by=request.user, **validated_data)

    def update(self, instance, validated_data):
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


class CommunicationAutomationRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationAutomationRun
        fields = ["id", "source_event", "source_object_type", "source_object_id", "status", "skip_reason", "communication", "error_message", "started_at", "finished_at"]
        read_only_fields = fields


class CommunicationPreferenceSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = CommunicationPreference
        fields = ["id", "patient", "patient_name", "preferred_channel", "allow_email", "allow_whatsapp", "allow_sms", "allow_reminders", "allow_financial_notices", "allow_form_requests", "allowed_start_time", "allowed_end_time", "timezone", "general_opt_out", "opt_out_reason", "opted_out_at", "consent_source", "consented_at", "send_to_guardian", "created_at", "updated_at"]
        read_only_fields = ["patient", "patient_name", "opted_out_at", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        request = self.context["request"]
        if validated_data.get("general_opt_out") and not instance.general_opt_out:
            validated_data["opted_out_at"] = timezone.now()
        if validated_data.get("general_opt_out") is False:
            validated_data["opted_out_at"] = None
        validated_data["consent_recorded_by"] = request.user
        return super().update(instance, validated_data)


class InAppNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InAppNotification
        fields = ["id", "title", "message", "notification_type", "priority", "internal_url", "is_read", "read_at", "created_at", "expires_at"]
        read_only_fields = fields


class CommunicationChannelConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationChannelConfig
        fields = ["channel", "provider", "is_active", "sender", "public_identifier", "connection_status", "last_validated_at", "metadata", "updated_at"]
        read_only_fields = ["provider", "connection_status", "last_validated_at", "updated_at"]

    def validate_metadata(self, value):
        forbidden = {"api_key", "token", "secret", "password", "access_token"}
        if any(str(key).lower() in forbidden for key in value):
            raise serializers.ValidationError("Segredos não podem ser enviados por esta API.")
        return value
