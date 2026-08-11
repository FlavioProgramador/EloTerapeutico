"""Serializers de registro de pagamentos."""

from django.utils import timezone
from rest_framework import serializers

from apps.finances.models import FinancialTransaction


class MarkAsPaidSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(
        choices=FinancialTransaction.PaymentMethod.choices,
        required=False,
        default=FinancialTransaction.PaymentMethod.PIX,
    )
    paid_at = serializers.DateTimeField(required=False, allow_null=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)

    def validate_paid_at(self, value):
        if value and value > timezone.now():
            raise serializers.ValidationError(
                "A data de pagamento não pode estar no futuro."
            )
        return value

    def validate(self, attrs):
        attrs["paid_at"] = attrs.get("paid_at") or timezone.now()
        return attrs
