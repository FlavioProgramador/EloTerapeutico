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
        if hasattr(obj, "_prefetched_objects_cache") and "payments" in obj._prefetched_objects_cache:
            return sum(
                1
                for p in obj.payments.all()
                if p.status in [Payment.Status.CONFIRMED, Payment.Status.RECEIVED]
            )
        return obj.payments.filter(
            status__in=[Payment.Status.CONFIRMED, Payment.Status.RECEIVED]
        ).count()

    def get_next_due_date(self, obj):
        if hasattr(obj, "_prefetched_objects_cache") and "payments" in obj._prefetched_objects_cache:
            pending_payments = [
                p
                for p in obj.payments.all()
                if p.status in [Payment.Status.PENDING, Payment.Status.OVERDUE]
                and p.due_date is not None
            ]
            if pending_payments:
                return min(pending_payments, key=lambda p: p.due_date).due_date
            return None
        payment = (
            obj.payments.filter(
                status__in=[Payment.Status.PENDING, Payment.Status.OVERDUE]
            )
            .order_by("due_date")
            .first()
        )
        return payment.due_date if payment else None
