from __future__ import annotations

from rest_framework import serializers

from apps.billing.models import BillingOrder, Payment

from .catalog import PlanPriceSerializer


class BillingOrderSerializer(serializers.ModelSerializer):
    plan_price = PlanPriceSerializer(read_only=True)
    paid_installments = serializers.SerializerMethodField()
    next_due_date = serializers.SerializerMethodField()

    class Meta:
        model = BillingOrder
        fields = [
            "public_id",
            "status",
            "billing_model",
            "billing_interval",
            "currency",
            "total_amount",
            "discount_amount",
            "installment_count",
            "installment_amount_estimate",
            "paid_installments",
            "next_due_date",
            "plan_price",
            "confirmed_at",
            "created_at",
            "updated_at",
        ]

    def get_paid_installments(self, obj):
        prefetched = getattr(obj, "_prefetched_objects_cache", {})
        if "payments" in prefetched:
            return sum(
                1
                for payment in prefetched["payments"]
                if payment.status in (Payment.Status.CONFIRMED, Payment.Status.RECEIVED)
            )
        return obj.payments.filter(
            status__in=[Payment.Status.CONFIRMED, Payment.Status.RECEIVED]
        ).count()

    def get_next_due_date(self, obj):
        prefetched = getattr(obj, "_prefetched_objects_cache", {})
        if "payments" in prefetched:
            pending = [
                payment
                for payment in prefetched["payments"]
                if payment.status in (Payment.Status.PENDING, Payment.Status.OVERDUE)
                and payment.due_date is not None
            ]
            if not pending:
                return None
            pending.sort(key=lambda p: p.due_date)
            return pending[0].due_date

        payment = (
            obj.payments.filter(
                status__in=[Payment.Status.PENDING, Payment.Status.OVERDUE]
            )
            .order_by("due_date")
            .first()
        )
        return payment.due_date if payment else None
