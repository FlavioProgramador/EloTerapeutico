from __future__ import annotations

from rest_framework import serializers

from apps.billing.models import Plan, Subscription

from .catalog import PlanSerializer
from .orders import BillingOrderSerializer


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    billing_order = BillingOrderSerializer(read_only=True)
    has_access = serializers.BooleanField(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "plan",
            "billing_order",
            "status",
            "has_access",
            "started_at",
            "access_starts_at",
            "access_ends_at",
            "trial_ends_at",
            "current_period_start",
            "current_period_end",
            "grace_period_ends_at",
            "cancel_at_period_end",
            "canceled_at",
            "suspended_at",
            "reactivated_at",
            "gateway_name",
            "gateway_status",
            "created_at",
            "updated_at",
        ]


class CreateSubscriptionSerializer(serializers.Serializer):
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.filter(is_active=True),
        source="plan",
    )


class ChangePlanSerializer(CreateSubscriptionSerializer):
    pass
