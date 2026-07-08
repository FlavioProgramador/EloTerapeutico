"""Serializers de mensalidades recorrentes."""

from urllib.parse import urlparse

from django.db import transaction
from rest_framework import serializers

from ..models import FinancialTransaction, MonthlySubscription


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

    def validate_payment_link(self, value):
        if value and urlparse(value).scheme != "https":
            raise serializers.ValidationError("O link de pagamento deve utilizar HTTPS.")
        return value

    def validate(self, attrs):
        request = self.context["request"]
        patient = attrs.get("patient", getattr(self.instance, "patient", None))
        if patient and request.user.is_therapist and patient.therapist_id != request.user.pk:
            raise serializers.ValidationError(
                {"patient": "Este paciente não pertence ao seu cadastro."}
            )
        first_date = attrs.get(
            "first_appointment_date",
            getattr(self.instance, "first_appointment_date", None),
        )
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if first_date and end_date and end_date < first_date:
            raise serializers.ValidationError(
                {"end_date": "A data final deve ser posterior ao primeiro atendimento."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context["request"]
        patient = validated_data["patient"]
        validated_data["therapist"] = (
            request.user if request.user.is_therapist else patient.therapist
        )
        subscription = super().create(validated_data)
        if subscription.first_due_date:
            FinancialTransaction.objects.get_or_create(
                subscription=subscription,
                due_date=subscription.first_due_date,
                defaults={
                    "therapist": subscription.therapist,
                    "patient": subscription.patient,
                    "transaction_type": FinancialTransaction.TransactionType.INCOME,
                    "category": FinancialTransaction.Category.SUBSCRIPTION,
                    "source": FinancialTransaction.Source.SUBSCRIPTION,
                    "amount": subscription.monthly_amount,
                    "payment_method": subscription.preferred_payment_method,
                    "payment_link": subscription.payment_link,
                    "description": f"Mensalidade - {subscription.patient.full_name}",
                },
            )
        return subscription
