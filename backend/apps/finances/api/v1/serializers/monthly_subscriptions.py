"""Serializers de mensalidades recorrentes."""

from urllib.parse import urlparse

from rest_framework import serializers

from apps.finances.models import MonthlySubscription
from apps.finances.selectors import selectable_patients_for_finance


class MonthlySubscriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    therapist_name = serializers.CharField(source="therapist.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    frequency_display = serializers.CharField(source="get_frequency_display", read_only=True)

    class Meta:
        model = MonthlySubscription
        fields = (
            "id",
            "patient",
            "patient_name",
            "therapist",
            "therapist_name",
            "status",
            "status_display",
            "frequency",
            "frequency_display",
            "weekday",
            "appointment_time",
            "first_appointment_date",
            "duration_minutes",
            "timezone",
            "end_date",
            "occurrence_limit",
            "monthly_amount",
            "due_day",
            "first_due_date",
            "next_billing_date",
            "reminder_days_before",
            "preferred_payment_method",
            "payment_link",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "therapist",
            "next_billing_date",
            "created_at",
            "updated_at",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        organization = getattr(request, "organization", None)
        self.fields["patient"].queryset = selectable_patients_for_finance(
            organization=organization
        )

    def validate_payment_link(self, value):
        if value and urlparse(value).scheme != "https":
            raise serializers.ValidationError(
                "O link de pagamento deve utilizar HTTPS."
            )
        return value

    def validate(self, attrs):
        first_date = attrs.get(
            "first_appointment_date",
            getattr(self.instance, "first_appointment_date", None),
        )
        end_date = attrs.get(
            "end_date",
            getattr(self.instance, "end_date", None),
        )
        if first_date and end_date and end_date < first_date:
            raise serializers.ValidationError(
                {"end_date": "A data final deve ser posterior ao primeiro atendimento."}
            )
        return attrs


class MonthlySubscriptionStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=MonthlySubscription.Status.choices)
