"""Serializers do módulo financeiro."""

from decimal import Decimal
from urllib.parse import urlparse

from django.utils import timezone
from rest_framework import serializers

from ..models import FinancialTransaction


class PatientNestedSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(read_only=True)


class AppointmentNestedSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    start_time = serializers.DateTimeField(read_only=True)
    end_time = serializers.DateTimeField(read_only=True)


class TransactionListSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(source="get_transaction_type_display", read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    payment_method_display = serializers.CharField(source="get_payment_method_display", read_only=True)
    payment_status_display = serializers.CharField(source="get_payment_status_display", read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True, allow_null=True)
    is_overdue = serializers.BooleanField(read_only=True)
    outstanding_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = FinancialTransaction
        fields = (
            "id",
            "patient",
            "appointment",
            "patient_name",
            "transaction_type",
            "transaction_type_display",
            "category",
            "category_display",
            "source",
            "amount",
            "paid_amount",
            "outstanding_amount",
            "payment_method",
            "payment_method_display",
            "payment_status",
            "payment_status_display",
            "due_date",
            "paid_at",
            "description",
            "beneficiary",
            "payment_link",
            "is_recurring",
            "recurrence_frequency",
            "is_overdue",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class TransactionDetailSerializer(TransactionListSerializer):
    patient_detail = PatientNestedSerializer(source="patient", read_only=True)
    appointment_detail = AppointmentNestedSerializer(source="appointment", read_only=True)

    class Meta(TransactionListSerializer.Meta):
        fields = TransactionListSerializer.Meta.fields + (
            "patient_detail",
            "appointment_detail",
            "recurrence_end_date",
            "receipt_url",
            "subscription",
        )


class TransactionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialTransaction
        fields = (
            "id",
            "patient",
            "appointment",
            "subscription",
            "transaction_type",
            "category",
            "source",
            "amount",
            "payment_method",
            "payment_status",
            "due_date",
            "paid_at",
            "description",
            "beneficiary",
            "payment_link",
            "receipt_url",
            "is_recurring",
            "recurrence_frequency",
            "recurrence_end_date",
        )
        read_only_fields = ("id", "source", "subscription")

    def validate_amount(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("O valor deve ser maior que zero.")
        return value

    def validate_payment_link(self, value: str) -> str:
        if value and urlparse(value).scheme != "https":
            raise serializers.ValidationError("O link de pagamento deve utilizar HTTPS.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None
        patient = attrs.get("patient", getattr(self.instance, "patient", None))
        appointment = attrs.get("appointment", getattr(self.instance, "appointment", None))

        if user and user.is_therapist:
            if patient and patient.therapist_id != user.pk:
                raise serializers.ValidationError({"patient": "Este paciente não pertence ao seu cadastro."})
            if appointment and appointment.therapist_id != user.pk:
                raise serializers.ValidationError({"appointment": "Esta consulta não pertence ao seu cadastro."})

        status_value = attrs.get("payment_status", getattr(self.instance, "payment_status", None))
        if status_value == FinancialTransaction.PaymentStatus.PAID and not attrs.get("paid_at", getattr(self.instance, "paid_at", None)):
            attrs["paid_at"] = timezone.now()
        if attrs.get("is_recurring") and not attrs.get("recurrence_frequency", getattr(self.instance, "recurrence_frequency", None)):
            raise serializers.ValidationError({"recurrence_frequency": "Informe a frequência da recorrência."})
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        patient = validated_data.get("patient")
        validated_data["therapist"] = request.user if request.user.is_therapist else patient.therapist
        if validated_data.get("payment_status") == FinancialTransaction.PaymentStatus.PAID:
            validated_data["paid_amount"] = validated_data["amount"]
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get("payment_status") == FinancialTransaction.PaymentStatus.PAID:
            validated_data["paid_amount"] = validated_data.get("amount", instance.amount)
        return super().update(instance, validated_data)


class MonthlySummarySerializer(serializers.Serializer):
    year = serializers.IntegerField(read_only=True)
    month = serializers.IntegerField(read_only=True)
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_expense = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_pending = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    transaction_count = serializers.IntegerField(read_only=True)


class MarkAsPaidSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=FinancialTransaction.PaymentMethod.choices, required=False, default=FinancialTransaction.PaymentMethod.PIX)
    paid_at = serializers.DateTimeField(required=False, allow_null=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)

    def validate_paid_at(self, value):
        if value and value > timezone.now():
            raise serializers.ValidationError("A data de pagamento não pode estar no futuro.")
        return value

    def validate(self, attrs):
        attrs["paid_at"] = attrs.get("paid_at") or timezone.now()
        return attrs
