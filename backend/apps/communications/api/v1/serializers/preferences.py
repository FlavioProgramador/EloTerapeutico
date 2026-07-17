from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.communications.models import CommunicationPreference


class CommunicationPreferenceSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = CommunicationPreference
        fields = [
            "id",
            "patient",
            "patient_name",
            "preferred_channel",
            "allow_email",
            "allow_whatsapp",
            "allow_sms",
            "allow_reminders",
            "allow_financial_notices",
            "allow_form_requests",
            "allowed_start_time",
            "allowed_end_time",
            "timezone",
            "general_opt_out",
            "opt_out_reason",
            "opted_out_at",
            "consent_source",
            "consented_at",
            "send_to_guardian",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "patient",
            "patient_name",
            "opted_out_at",
            "created_at",
            "updated_at",
        ]

    def update(self, instance, validated_data):
        request = self.context["request"]
        if validated_data.get("general_opt_out") and not instance.general_opt_out:
            validated_data["opted_out_at"] = timezone.now()
        if validated_data.get("general_opt_out") is False:
            validated_data["opted_out_at"] = None
        validated_data["consent_recorded_by"] = request.user
        return super().update(instance, validated_data)
