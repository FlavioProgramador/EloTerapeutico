"""
apps/financeiro/serializers.py
Serializers do módulo financeiro para listagem, criação, edição e
ações especiais (resumo mensal, marcar como pago).
"""

from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from .models import FinancialTransaction


# ── Serializer auxiliar de paciente (nested) ─────────────────────────────────
class _PatientNestedSerializer(serializers.Serializer):
    """Representação mínima do paciente para leitura em contexto financeiro."""

    id = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(read_only=True)


# ── Serializer auxiliar de consulta (nested) ─────────────────────────────────
class _AppointmentNestedSerializer(serializers.Serializer):
    """Representação mínima da consulta para leitura em contexto financeiro."""

    id = serializers.IntegerField(read_only=True)
    start_time = serializers.DateTimeField(read_only=True)
    end_time = serializers.DateTimeField(read_only=True)


# ─────────────────────────────────────────────────────────────────────────────
# 1. TransactionListSerializer – campos resumidos para listagem
# ─────────────────────────────────────────────────────────────────────────────
class TransactionListSerializer(serializers.ModelSerializer):
    """
    Serializer leve para listagem paginada de transações.
    Expõe apenas os campos essenciais para exibição em tabelas/cards.
    """

    transaction_type_display = serializers.CharField(
        source="get_transaction_type_display", read_only=True
    )
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )
    payment_status_display = serializers.CharField(
        source="get_payment_status_display", read_only=True
    )
    patient_name = serializers.SerializerMethodField()
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = FinancialTransaction
        fields = (
            "id",
            "transaction_type",
            "transaction_type_display",
            "category",
            "category_display",
            "amount",
            "payment_method",
            "payment_method_display",
            "payment_status",
            "payment_status_display",
            "patient_name",
            "due_date",
            "paid_at",
            "is_overdue",
            "created_at",
        )
        read_only_fields = fields

    def get_patient_name(self, obj) -> str | None:
        """Retorna o nome do paciente ou None."""
        if obj.patient_id:
            return obj.patient.full_name
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 2. TransactionDetailSerializer – todos os campos com nested
# ─────────────────────────────────────────────────────────────────────────────
class TransactionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer completo para exibição do detalhe de uma transação.
    Inclui objetos nested de paciente e consulta para evitar IDs soltos.
    """

    transaction_type_display = serializers.CharField(
        source="get_transaction_type_display", read_only=True
    )
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )
    payment_status_display = serializers.CharField(
        source="get_payment_status_display", read_only=True
    )

    is_overdue = serializers.BooleanField(read_only=True)

    # Representações nested (somente leitura)
    patient_detail = _PatientNestedSerializer(source="patient", read_only=True)
    appointment_detail = _AppointmentNestedSerializer(
        source="appointment", read_only=True
    )

    class Meta:
        model = FinancialTransaction
        fields = (
            "id",
            # Tipo e categoria
            "transaction_type",
            "transaction_type_display",
            "category",
            "category_display",
            # Valor e pagamento
            "amount",
            "payment_method",
            "payment_method_display",
            "payment_status",
            "payment_status_display",
            "is_overdue",
            # Relacionamentos
            "patient",
            "patient_detail",
            "appointment",
            "appointment_detail",
            # Datas
            "due_date",
            "paid_at",
            # Extras
            "description",
            "receipt_url",
            # Auditoria
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


# ─────────────────────────────────────────────────────────────────────────────
# 3. TransactionCreateUpdateSerializer – criação e edição
# ─────────────────────────────────────────────────────────────────────────────
class TransactionCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação (POST) e edição (PUT/PATCH) de transações.
    O campo 'therapist' é preenchido automaticamente com request.user.
    """

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
            "receipt_url",
        )
        read_only_fields = ("id",)

    # ── Validações ────────────────────────────────────────────────────────────
    def validate_amount(self, value: Decimal) -> Decimal:
        """Garante que o valor da transação seja positivo."""
        if value <= 0:
            raise serializers.ValidationError(
                "O valor da transação deve ser maior que zero."
            )
        return value

    def validate(self, attrs: dict) -> dict:
        """
        Validação cruzada:
        - Se payment_status='paid', paid_at deve estar preenchido.
        - Garante que o appointment pertence ao mesmo terapeuta.
        """
        status = attrs.get(
            "payment_status",
            getattr(self.instance, "payment_status", None),
        )
        paid_at = attrs.get(
            "paid_at",
            getattr(self.instance, "paid_at", None),
        )

        if status == FinancialTransaction.PaymentStatus.PAID and not paid_at:
            # Se marcando como pago sem informar paid_at, seta automaticamente
            attrs["paid_at"] = timezone.now()

        # Valida que o appointment pertence ao terapeuta autenticado
        appointment = attrs.get("appointment")
        if appointment:
            request = self.context.get("request")
            if request and appointment.therapist_id != request.user.pk:
                raise serializers.ValidationError(
                    {"appointment": "Esta consulta não pertence ao seu cadastro."}
                )

        # Valida que o patient pertence ao terapeuta autenticado
        patient = attrs.get("patient")
        if patient:
            request = self.context.get("request")
            if request and patient.therapist_id != request.user.pk:
                raise serializers.ValidationError(
                    {"patient": "Este paciente não pertence ao seu cadastro."}
                )

        return attrs

    def create(self, validated_data: dict) -> FinancialTransaction:
        """Associa automaticamente o terapeuta ao usuário autenticado."""
        validated_data["therapist"] = self.context["request"].user
        return super().create(validated_data)


# ─────────────────────────────────────────────────────────────────────────────
# 4. MonthlySummarySerializer – resumo mensal
# ─────────────────────────────────────────────────────────────────────────────
class MonthlySummarySerializer(serializers.Serializer):
    """
    Serializer de saída para o endpoint GET /financeiro/summary/.
    Descreve o resumo financeiro de um mês específico.
    """

    year = serializers.IntegerField(read_only=True)
    month = serializers.IntegerField(read_only=True)
    total_income = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    total_expense = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    balance = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    total_pending = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    transaction_count = serializers.IntegerField(read_only=True)


# ─────────────────────────────────────────────────────────────────────────────
# 5. MarkAsPaidSerializer – apenas paid_at e payment_method
# ─────────────────────────────────────────────────────────────────────────────
class MarkAsPaidSerializer(serializers.ModelSerializer):
    """
    Serializer para a ação PATCH /financeiro/{id}/pay/.
    Permite informar apenas o método de pagamento e, opcionalmente,
    a data/hora do pagamento (padrão: agora).
    """

    paid_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Data/hora do pagamento. Se omitido, usa o momento atual.",
    )

    class Meta:
        model = FinancialTransaction
        fields = ("payment_method", "paid_at")

    def validate_paid_at(self, value):
        """Não permite data de pagamento no futuro."""
        if value and value > timezone.now():
            raise serializers.ValidationError(
                "A data de pagamento não pode ser no futuro."
            )
        return value

    def validate(self, attrs: dict) -> dict:
        """Garante que paid_at seja preenchido, usando agora() como fallback."""
        if not attrs.get("paid_at"):
            attrs["paid_at"] = timezone.now()
        return attrs
