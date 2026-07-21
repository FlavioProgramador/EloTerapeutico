"""Serializers de transações financeiras."""

from decimal import Decimal
from urllib.parse import urlparse

from rest_framework import serializers

from apps.finances.models import FinancialTransaction
from apps.patients.models import Patient
from apps.scheduling.models import Appointment


class PatientNestedSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(read_only=True)


class AppointmentNestedSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    start_time = serializers.DateTimeField(read_only=True)
    end_time = serializers.DateTimeField(read_only=True)


class TransactionListSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(
        source="get_transaction_type_display",
        read_only=True,
    )
    category_display = serializers.CharField(
        source="get_category_display",
        read_only=True,
    )
    payment_method_display = serializers.CharField(
        source="get_payment_method_display",
        read_only=True,
    )
    payment_status_display = serializers.CharField(
        source="get_payment_status_display",
        read_only=True,
    )
    patient_name = serializers.CharField(
        source="patient.full_name",
        read_only=True,
        allow_null=True,
    )
    is_overdue = serializers.BooleanField(read_only=True)
    outstanding_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

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
    appointment_detail = AppointmentNestedSerializer(
        source="appointment",
        read_only=True,
    )

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
            "transaction_type",
            "category",
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
        read_only_fields = ("id",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        organization = getattr(request, "organization", None)
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

    def validate_amount(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("O valor deve ser maior que zero.")
        return value

    def _validate_https(self, value: str) -> str:
        if value and urlparse(value).scheme != "https":
            raise serializers.ValidationError("O link deve utilizar HTTPS.")
        return value

    def validate_payment_link(self, value: str) -> str:
        return self._validate_https(value)

    def validate_receipt_url(self, value: str) -> str:
        return self._validate_https(value)

    def validate(self, attrs):
        if attrs.get("is_recurring") and not attrs.get(
            "recurrence_frequency",
            getattr(self.instance, "recurrence_frequency", None),
        ):
            raise serializers.ValidationError(
                {"recurrence_frequency": "Informe a frequência da recorrência."}
            )
        return attrs
