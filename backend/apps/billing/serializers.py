from rest_framework import serializers

from apps.billing.models import Payment, Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "currency",
            "billing_cycle",
            "max_patients",
            "max_storage_mb",
            "features",
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


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "plan",
            "status",
            "started_at",
            "trial_ends_at",
            "current_period_start",
            "current_period_end",
            "canceled_at",
            "gateway_name",
            "gateway_status",
            "created_at",
            "updated_at",
        ]


class CreateSubscriptionSerializer(serializers.Serializer):
    plan_id = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.filter(is_active=True), source="plan")


class ChangePlanSerializer(CreateSubscriptionSerializer):
    pass


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "amount",
            "currency",
            "status",
            "due_date",
            "paid_at",
            "invoice_url",
            "bank_slip_url",
            "created_at",
        ]
