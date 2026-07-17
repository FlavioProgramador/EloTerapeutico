from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from rest_framework import serializers

from apps.billing.models import Plan, PlanPrice

MONEY = Decimal("0.01")


class PlanPriceSerializer(serializers.ModelSerializer):
    installment_amount_from_max = serializers.SerializerMethodField()
    available = serializers.SerializerMethodField()

    class Meta:
        model = PlanPrice
        fields = [
            "id",
            "name",
            "slug",
            "currency",
            "total_amount",
            "billing_interval",
            "billing_model",
            "discount_percentage",
            "installments_enabled",
            "min_installments",
            "max_installments",
            "installment_amount_from_max",
            "trial_days",
            "available",
        ]

    def get_installment_amount_from_max(self, obj):
        count = obj.max_installments if obj.installments_enabled else 1
        amount = obj.total_amount / Decimal(count)
        return str(amount.quantize(MONEY, rounding=ROUND_HALF_UP))

    def get_available(self, obj):
        return obj.is_available()


class PlanSerializer(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()
    prices = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "max_patients",
            "max_storage_mb",
            "features",
            "prices",
            "price",
            "currency",
            "billing_cycle",
        ]

    def get_features(self, obj):
        return {
            "agenda": obj.has_agenda,
            "patients": obj.has_patients,
            "clinical_records": obj.has_clinical_records,
            "financial": obj.has_financial,
            "documents": obj.has_documents,
            "forms": obj.has_forms,
            "reports": obj.has_reports,
            "ai": obj.has_ai,
        }

    def get_prices(self, obj):
        prices = [price for price in obj.prices.all() if price.is_available()]
        return PlanPriceSerializer(prices, many=True).data
