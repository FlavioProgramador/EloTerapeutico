from __future__ import annotations

from rest_framework import serializers

from apps.billing.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    order_public_id = serializers.UUIDField(
        source="billing_order.public_id",
        read_only=True,
    )
    installment_label = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            "id",
            "order_public_id",
            "amount",
            "net_amount",
            "interest_amount",
            "fine_amount",
            "discount_amount",
            "currency",
            "billing_type",
            "status",
            "due_date",
            "original_due_date",
            "paid_at",
            "confirmed_at",
            "credit_at",
            "refunded_at",
            "installment_number",
            "installment_count",
            "installment_label",
            "invoice_number",
            "invoice_url",
            "bank_slip_url",
            "transaction_receipt_url",
            "pix_qr_code",
            "pix_copy_paste",
            "created_at",
            "updated_at",
        ]

    def get_installment_label(self, obj):
        if obj.installment_number:
            return f"Parcela {obj.installment_number} de {obj.installment_count}"
        return "Pagamento à vista"
