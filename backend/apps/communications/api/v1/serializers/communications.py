from __future__ import annotations

import uuid

from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from apps.communications.models import (
    Communication,
    CommunicationAttempt,
    CommunicationRecipient,
    CommunicationTemplate,
)
from apps.communications.services import create_communication
from apps.communications.validators import plain_text_to_safe_html
from apps.organizations.models import OrganizationMembership
from apps.patients.models import Patient
from apps.patients.services.access_control import patient_access_q
from apps.scheduling.models import Appointment


class CommunicationRecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationRecipient
        fields = [
            "id",
            "recipient_type",
            "name",
            "destination_masked",
            "channel",
            "status",
            "blocked_reason",
        ]
        read_only_fields = fields


class CommunicationAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationAttempt
        fields = [
            "id",
            "attempt_number",
            "provider",
            "status",
            "external_id",
            "response_code",
            "error_code",
            "error_message",
            "started_at",
            "finished_at",
            "next_retry_at",
            "latency_ms",
            "created_at",
        ]
        read_only_fields = fields


class CommunicationListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    created_by_name = serializers.CharField(
        source="created_by.full_name",
        read_only=True,
    )
    recipient = serializers.SerializerMethodField()

    class Meta:
        model = Communication
        fields = [
            "public_id",
            "patient",
            "patient_name",
            "category",
            "channel",
            "subject",
            "status",
            "priority",
            "scheduled_at",
            "sent_at",
            "created_at",
            "created_by_name",
            "recipient",
            "source_event",
        ]

    def get_recipient(self, obj):
        recipient = next(iter(obj.recipients.all()), None)
        return recipient.destination_masked if recipient else ""


class CommunicationDetailSerializer(serializers.ModelSerializer):
    recipients = CommunicationRecipientSerializer(many=True, read_only=True)
    attempts = CommunicationAttemptSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    template_name = serializers.CharField(source="template.name", read_only=True)
    created_by_name = serializers.CharField(
        source="created_by.full_name",
        read_only=True,
    )

    class Meta:
        model = Communication
        fields = [
            "public_id",
            "patient",
            "patient_name",
            "appointment",
            "form_submission",
            "document",
            "financial_transaction",
            "direction",
            "channel",
            "category",
            "status",
            "priority",
            "subject",
            "body",
            "body_html",
            "template",
            "template_name",
            "scheduled_at",
            "queued_at",
            "processing_started_at",
            "sent_at",
            "delivered_at",
            "read_at",
            "responded_at",
            "failed_at",
            "canceled_at",
            "expires_at",
            "source_event",
            "source_object_type",
            "source_object_id",
            "provider_name",
            "created_at",
            "updated_at",
            "created_by_name",
            "recipients",
            "attempts",
            "metadata",
        ]
        read_only_fields = fields


class CommunicationCreateSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField(required=False, allow_null=True)
    appointment_id = serializers.IntegerField(required=False, allow_null=True)
    channel = serializers.ChoiceField(choices=Communication.Channel.choices)
    category = serializers.ChoiceField(
        choices=Communication.Category.choices,
        default=Communication.Category.OTHER,
    )
    template_id = serializers.IntegerField(required=False, allow_null=True)
    subject = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
    )
    body = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=10000,
    )
    variables = serializers.JSONField(required=False, default=dict)
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)
    priority = serializers.ChoiceField(
        choices=Communication.Priority.choices,
        default=Communication.Priority.NORMAL,
    )
    recipient_type = serializers.ChoiceField(
        choices=CommunicationRecipient.RecipientType.choices,
        required=False,
        allow_null=True,
    )
    draft = serializers.BooleanField(default=False)

    def validate(self, attrs):
        request = self.context["request"]
        organization = getattr(request, "organization", None)
        membership = getattr(request, "organization_membership", None)
        if organization is None or membership is None:
            raise serializers.ValidationError(
                {"organization": "Selecione uma organização."}
            )

        patient_id = attrs.get("patient_id")
        appointment_id = attrs.get("appointment_id")
        patient = None
        appointment = None

        if patient_id:
            patient = (
                Patient.objects.filter(
                    pk=patient_id,
                    organization=organization,
                    deleted_at__isnull=True,
                )
                .filter(patient_access_q(request.user, membership=membership))
                .distinct()
                .first()
            )
            if patient is None:
                raise serializers.ValidationError(
                    {"patient_id": "Paciente não encontrado nesta organização."}
                )

        if appointment_id:
            appointment = Appointment.objects.filter(
                pk=appointment_id,
                organization=organization,
            ).first()
            if appointment is None:
                raise serializers.ValidationError(
                    {"appointment_id": "Consulta não encontrada nesta organização."}
                )
            if membership.role == OrganizationMembership.Role.THERAPIST and (
                appointment.therapist_id != request.user.pk
            ):
                raise serializers.ValidationError(
                    {"appointment_id": "Consulta não autorizada."}
                )
            if patient is not None and appointment.patient_id != patient.pk:
                raise serializers.ValidationError(
                    {"appointment_id": "A consulta pertence a outro paciente."}
                )
            patient = patient or appointment.patient

        if attrs["channel"] != Communication.Channel.IN_APP and patient is None:
            raise serializers.ValidationError(
                {"patient_id": "Selecione um paciente para este canal."}
            )

        template = None
        template_id = attrs.get("template_id")
        if template_id:
            template = CommunicationTemplate.objects.filter(
                Q(
                    organization=organization,
                    is_system_template=False,
                    is_archived=False,
                )
                | Q(
                    organization__isnull=True,
                    owner__isnull=True,
                    is_system_template=True,
                    is_archived=False,
                ),
                pk=template_id,
                is_active=True,
            ).first()
            if template is None:
                raise serializers.ValidationError(
                    {"template_id": "Template não encontrado."}
                )
            if template.channel != attrs["channel"]:
                raise serializers.ValidationError(
                    {"template_id": "O template não pertence ao canal selecionado."}
                )
        elif not attrs.get("body", "").strip():
            raise serializers.ValidationError(
                {"body": "Informe o conteúdo ou selecione um template."}
            )

        attrs["organization"] = organization
        attrs["patient"] = patient
        attrs["appointment"] = appointment
        attrs["template"] = template
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        validated_data.pop("patient_id", None)
        validated_data.pop("appointment_id", None)
        validated_data.pop("template_id", None)
        idempotency_key = request.headers.get("Idempotency-Key") or (
            f"manual:{validated_data['organization'].pk}:{request.user.pk}:"
            f"{uuid.uuid4().hex}"
        )
        return create_communication(
            owner=request.user,
            created_by=request.user,
            idempotency_key=idempotency_key,
            source_event="manual",
            **validated_data,
        )


class CommunicationDraftUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Communication
        fields = ["subject", "body", "category", "priority", "scheduled_at"]

    def validate(self, attrs):
        if self.instance.status != Communication.Status.DRAFT:
            raise serializers.ValidationError(
                "Somente rascunhos podem ser editados."
            )
        body = attrs.get("body", self.instance.body)
        if not str(body).strip():
            raise serializers.ValidationError(
                {"body": "O conteúdo é obrigatório."}
            )
        scheduled_at = attrs.get("scheduled_at")
        if scheduled_at and scheduled_at <= timezone.now():
            raise serializers.ValidationError(
                {"scheduled_at": "A data deve estar no futuro."}
            )
        return attrs

    def update(self, instance, validated_data):
        if "body" in validated_data:
            instance.body_html = plain_text_to_safe_html(validated_data["body"])
        return super().update(instance, validated_data)
