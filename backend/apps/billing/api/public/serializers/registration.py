from __future__ import annotations

from rest_framework import serializers

from apps.billing.models import PlanPrice


class PlanRegistrationSerializer(serializers.Serializer):
    access_mode = serializers.ChoiceField(
        choices=("TRIAL", "PAID"),
        default="TRIAL",
    )
    plan = serializers.SlugField(required=False, allow_blank=True)
    plan_slug = serializers.SlugField(required=False, allow_blank=True)
    plan_price_id = serializers.IntegerField(required=False)
    plan_price_slug = serializers.SlugField(required=False, allow_blank=True)
    billing_cycle = serializers.ChoiceField(
        choices=("MONTHLY", "YEARLY"),
        required=False,
    )
    payment_mode = serializers.ChoiceField(
        choices=("RECURRING", "ONE_TIME", "INSTALLMENT"),
        required=False,
    )

    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    crp = serializers.CharField(required=False, allow_blank=True)
    crp_number = serializers.CharField(required=False, allow_blank=True)
    specialty = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    terms_accepted = serializers.BooleanField()
    privacy_accepted = serializers.BooleanField()

    def validate(self, attrs):
        if not attrs.get("terms_accepted"):
            raise serializers.ValidationError(
                {"terms_accepted": "É necessário aceitar os Termos de Uso."}
            )
        if not attrs.get("privacy_accepted"):
            raise serializers.ValidationError(
                {
                    "privacy_accepted": (
                        "É necessário aceitar a Política de Privacidade."
                    )
                }
            )

        plan_requested = bool(
            attrs.get("plan_price_id")
            or attrs.get("plan_price_slug")
            or attrs.get("plan_slug")
            or attrs.get("plan")
        )
        if not plan_requested:
            attrs["plan_price"] = None
            return attrs

        prices = PlanPrice.objects.select_related("plan").filter(
            is_active=True,
            plan__is_active=True,
        )
        price = None
        if attrs.get("plan_price_id"):
            price = prices.filter(pk=attrs["plan_price_id"]).first()
        elif attrs.get("plan_price_slug"):
            price = prices.filter(
                slug__iexact=attrs["plan_price_slug"]
            ).first()
        else:
            plan_slug = attrs.get("plan_slug") or attrs.get("plan")
            prices = prices.filter(plan__slug__iexact=plan_slug)
            if attrs.get("billing_cycle"):
                prices = prices.filter(
                    billing_interval=attrs["billing_cycle"]
                )
            if attrs.get("payment_mode"):
                prices = prices.filter(billing_model=attrs["payment_mode"])
            price = prices.order_by("total_amount", "billing_model").first()

        if not price or not price.is_available():
            raise serializers.ValidationError(
                {
                    "plan": (
                        "O plano ou a modalidade selecionada não está "
                        "disponível."
                    )
                }
            )
        attrs["plan_price"] = price
        return attrs
