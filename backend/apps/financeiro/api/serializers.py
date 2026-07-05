"""Serializers públicos do módulo financeiro."""

from decimal import Decimal
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from apps.agenda.models import Appointment
from apps.patients.models import Patient

from ..models import (
    Charge,
    ChargeItem,
    FinancialAuditLog,
    FinancialCategory,
    FinancialTransaction,
    MonthlySubscription,
    Payment,
)


class _PatientNestedSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(read_only=True)


class _ProfessionalNestedSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(read_only=True)


class _AppointmentNestedSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    start_time = serializers.DateTimeField(read_only=True)
    end_time = serializers.DateTimeField(read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)
    session_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)


class PaymentSerializer(serializers.ModelSerializer):
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )

    class Meta:
        model = Payment
        fields = (
            "id",
            "amount",
            "payment_date",
            "payment_method",
            "payment_method_display",
            "reference",
            "notes",
            "created_at",
            "reversed_at",
            "reversal_reason",
        )
        read_only_fields = fields


class TransactionListSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(
        source="get_transaction_type_display", read_only=True
    )
    category_display = serializers.SerializerMethodField()
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )
    payment_status_display = serializers.CharField(
        source="get_payment_status_display", read_only=True
    )
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    professional_name = serializers.CharField(source="therapist.full_name", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    paid_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    outstanding_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = FinancialTransaction
        fields = (
            "id",
            "transaction_type",
            "transaction_type_display",
            "category",
            "category_ref",
            "category_display",
            "amount",
            "paid_amount",
            "outstanding_amount",
            "payment_method",
            "payment_method_display",
            "payment_status",
            "payment_status_display",
            "patient",
            "patient_name",
            "professional_name",
            "beneficiary",
            "due_date",
            "paid_at",
            "is_overdue",
            "source",
            "description",
            "is_recurring",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_category_display(self, obj) -> str:
        return obj.category_ref.name if obj.category_ref_id else obj.get_category_display()


class TransactionDetailSerializer(TransactionListSerializer):
    patient_detail = _PatientNestedSerializer(source="patient", read_only=True)
    appointment_detail = _AppointmentNestedSerializer(source="appointment", read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta(TransactionListSerializer.Meta):
        fields = TransactionListSerializer.Meta.fields + (
            "appointment",
            "patient_detail",
            "appointment_detail",
            "payment_link",
            "notes",
            "receipt_url",
            "payments",
            "canceled_at",
            "deleted_at",
        )


def _validate_https_url(value: str) -> str:
    if not value:
        return value
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise serializers.ValidationError("Informe uma URL HTTPS válida.")
    return value


class TransactionCreateUpdateSerializer(serializers.ModelSerializer):
    mark_as_paid = serializers.BooleanField(write_only=True, required=False, default=False)
    payment_date = serializers.DateTimeField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = FinancialTransaction
        fields = (
            "id",
            "patient",
            "appointment",
            "transaction_type",
            "category",
            "category_ref",
            "amount",
            "payment_method",
            "payment_status",
            "due_date",
            "paid_at",
            "payment_date",
            "description",
            "notes",
            "beneficiary",
            "payment_link",
            "receipt_url",
            "source",
            "is_recurring",
            "mark_as_paid",
        )
        read_only_fields = ("id", "source", "payment_status", "paid_at")
        extra_kwargs = {
            "description": {"required": True, "allow_blank": False, "max_length": 500},
        }

    def validate_amount(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("O valor deve ser maior que zero.")
        return value

    def validate_payment_link(self, value: str) -> str:
        return _validate_https_url(value)

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        patient = attrs.get("patient", getattr(self.instance, "patient", None))
        appointment = attrs.get("appointment", getattr(self.instance, "appointment", None))
        category_ref = attrs.get("category_ref", getattr(self.instance, "category_ref", None))

        if patient and patient.therapist_id != user.pk and not (
            user.is_admin_role or user.is_secretary
        ):
            raise serializers.ValidationError(
                {"patient": "Este paciente não pertence ao seu cadastro."}
            )
        if appointment and appointment.therapist_id != user.pk and not (
            user.is_admin_role or user.is_secretary
        ):
            raise serializers.ValidationError(
                {"appointment": "Esta sessão não pertence ao seu cadastro."}
            )
        if category_ref and category_ref.therapist_id != user.pk and not (
            user.is_admin_role or user.is_secretary
        ):
            raise serializers.ValidationError(
                {"category_ref": "Esta categoria não está disponível para este usuário."}
            )
        if appointment and patient and appointment.patient_id != patient.pk:
            raise serializers.ValidationError(
                {"appointment": "A sessão selecionada não pertence ao paciente informado."}
            )

        mark_as_paid = attrs.pop("mark_as_paid", False)
        payment_date = attrs.pop("payment_date", None)
        status = attrs.get(
            "payment_status",
            getattr(self.instance, "payment_status", FinancialTransaction.PaymentStatus.PENDING),
        )
        if mark_as_paid:
            attrs["payment_status"] = FinancialTransaction.PaymentStatus.PAID
            attrs["paid_at"] = payment_date or timezone.now()
        elif status == FinancialTransaction.PaymentStatus.PAID and not attrs.get(
            "paid_at", getattr(self.instance, "paid_at", None)
        ):
            attrs["paid_at"] = timezone.now()
        if attrs.get("paid_at") and attrs["paid_at"] > timezone.now():
            raise serializers.ValidationError(
                {"paid_at": "A data de pagamento não pode estar no futuro."}
            )
        return attrs

    def create(self, validated_data):
        actor = self.context["request"].user
        validated_data.update(therapist=actor, created_by=actor, updated_by=actor)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data["updated_by"] = self.context["request"].user
        return super().update(instance, validated_data)


class MarkAsPaidSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    payment_method = serializers.ChoiceField(
        choices=FinancialTransaction.PaymentMethod.choices,
        required=False,
        default=FinancialTransaction.PaymentMethod.PIX,
    )
    paid_at = serializers.DateTimeField(required=False, allow_null=True)
    reference = serializers.CharField(required=False, allow_blank=True, max_length=120)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("O valor deve ser maior que zero.")
        return value

    def validate_paid_at(self, value):
        if value and value > timezone.now():
            raise serializers.ValidationError("A data de pagamento não pode estar no futuro.")
        return value


class ReversePaymentSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=3, max_length=255)


class FinancialSummarySerializer(serializers.Serializer):
    year = serializers.IntegerField(required=False)
    month = serializers.IntegerField(required=False)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    received_period = serializers.DecimalField(max_digits=14, decimal_places=2)
    received_count = serializers.IntegerField()
    paid_expenses = serializers.DecimalField(max_digits=14, decimal_places=2)
    paid_expenses_count = serializers.IntegerField()
    receivable_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    receivable_count = serializers.IntegerField()
    payable_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    payable_count = serializers.IntegerField()
    overdue_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    overdue_receivable_count = serializers.IntegerField()
    overdue_payable_count = serializers.IntegerField()
    projected_balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_income = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_expense = serializers.DecimalField(max_digits=14, decimal_places=2)
    balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_pending = serializers.DecimalField(max_digits=14, decimal_places=2)
    transaction_count = serializers.IntegerField()


MonthlySummarySerializer = FinancialSummarySerializer


class FinancialCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialCategory
        fields = ("id", "name", "category_type", "color", "active", "created_at")
        read_only_fields = ("id", "created_at")

    def create(self, validated_data):
        validated_data["therapist"] = self.context["request"].user
        return super().create(validated_data)


class EligibleAppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    professional_name = serializers.CharField(source="therapist.full_name", read_only=True)

    class Meta:
        model = Appointment
        fields = (
            "id",
            "patient",
            "patient_name",
            "professional_name",
            "start_time",
            "end_time",
            "duration_minutes",
            "session_value",
        )
        read_only_fields = fields


class ChargeItemSerializer(serializers.ModelSerializer):
    appointment_detail = EligibleAppointmentSerializer(source="appointment", read_only=True)

    class Meta:
        model = ChargeItem
        fields = (
            "id",
            "appointment",
            "appointment_detail",
            "description",
            "quantity",
            "unit_amount",
            "total_amount",
        )
        read_only_fields = fields


class ChargeListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    professional_name = serializers.CharField(source="professional.full_name", read_only=True)
    amount = serializers.DecimalField(source="transaction.amount", max_digits=12, decimal_places=2, read_only=True)
    due_date = serializers.DateField(source="transaction.due_date", read_only=True)
    payment_status = serializers.CharField(source="transaction.payment_status", read_only=True)
    description = serializers.CharField(source="transaction.description", read_only=True)
    items_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = Charge
        fields = (
            "id",
            "patient",
            "patient_name",
            "professional",
            "professional_name",
            "transaction",
            "description",
            "amount",
            "due_date",
            "payment_status",
            "reference_month",
            "whatsapp_status",
            "items_count",
            "created_at",
        )
        read_only_fields = fields


class ChargeDetailSerializer(ChargeListSerializer):
    transaction_detail = TransactionDetailSerializer(source="transaction", read_only=True)
    items = ChargeItemSerializer(many=True, read_only=True)

    class Meta(ChargeListSerializer.Meta):
        fields = ChargeListSerializer.Meta.fields + ("transaction_detail", "items")


class ChargeCreateSerializer(serializers.Serializer):
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())
    professional = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.filter(role="therapist", is_active=True),
        required=False,
        allow_null=True,
    )
    appointment_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), min_length=1
    )
    due_date = serializers.DateField()
    description = serializers.CharField(required=False, allow_blank=True, max_length=500)
    payment_link = serializers.CharField(required=False, allow_blank=True, max_length=500)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    send_whatsapp = serializers.BooleanField(required=False, default=False)

    def validate_payment_link(self, value):
        return _validate_https_url(value)

    def validate(self, attrs):
        user = self.context["request"].user
        patient = attrs["patient"]
        professional = attrs.get("professional") or patient.therapist
        attrs["professional"] = professional
        if patient.therapist_id != professional.pk:
            raise serializers.ValidationError(
                {"professional": "O profissional não é responsável pelo paciente selecionado."}
            )
        if not (user.is_admin_role or user.is_secretary or user.pk == professional.pk):
            raise serializers.ValidationError("Você não pode criar cobranças para este profissional.")
        return attrs


class GenerateMonthlyChargesSerializer(serializers.Serializer):
    year = serializers.IntegerField(min_value=2020, max_value=2100)
    month = serializers.IntegerField(min_value=1, max_value=12)
    due_date = serializers.DateField()
    appointment_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False, allow_empty=True
    )


class MonthlySubscriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    professional_name = serializers.CharField(source="professional.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    frequency_display = serializers.CharField(source="get_frequency_display", read_only=True)

    class Meta:
        model = MonthlySubscription
        fields = (
            "id",
            "patient",
            "patient_name",
            "professional",
            "professional_name",
            "amount",
            "status",
            "status_display",
            "frequency",
            "frequency_display",
            "weekday",
            "time",
            "duration_minutes",
            "first_appointment_date",
            "billing_day",
            "first_charge_due_date",
            "payment_method",
            "payment_link",
            "whatsapp_reminder_days",
            "start_date",
            "end_date",
            "next_appointment_date",
            "next_charge_due_date",
            "generated_until",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "status",
            "next_appointment_date",
            "next_charge_due_date",
            "generated_until",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {"professional": {"required": False, "allow_null": True}}

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("O valor deve ser maior que zero.")
        return value

    def validate_billing_day(self, value):
        if not 1 <= value <= 28:
            raise serializers.ValidationError("Use um dia entre 1 e 28.")
        return value

    def validate_payment_link(self, value):
        return _validate_https_url(value)

    def validate(self, attrs):
        patient = attrs.get("patient", getattr(self.instance, "patient", None))
        professional = attrs.get(
            "professional", getattr(self.instance, "professional", None)
        )
        if patient and professional is None:
            professional = patient.therapist
            attrs["professional"] = professional
        request = self.context["request"]
        if patient and professional and patient.therapist_id != professional.pk:
            raise serializers.ValidationError(
                {"professional": "O profissional não é responsável por este paciente."}
            )
        if professional and not (
            request.user.is_admin_role
            or request.user.is_secretary
            or request.user.pk == professional.pk
        ):
            raise serializers.ValidationError("Profissional fora do seu escopo de acesso.")
        first_date = attrs.get(
            "first_appointment_date",
            getattr(self.instance, "first_appointment_date", None),
        )
        if first_date and first_date < timezone.localdate():
            raise serializers.ValidationError(
                {"first_appointment_date": "A primeira data não pode estar no passado."}
            )
        return attrs


class FinancialAuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.full_name", read_only=True)

    class Meta:
        model = FinancialAuditLog
        fields = (
            "id",
            "actor_name",
            "action",
            "entity_type",
            "entity_id",
            "metadata",
            "created_at",
        )
        read_only_fields = fields
