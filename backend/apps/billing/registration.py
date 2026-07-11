from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.billing.models import PlanPrice, Subscription
from apps.billing.serializers import PlanPriceSerializer, PlanSerializer, SubscriptionSerializer
from apps.users.api.serializers import RegisterSerializer, UserProfileSerializer

TRIAL_DAYS = 7


class PlanRegistrationSerializer(serializers.Serializer):
    access_mode = serializers.ChoiceField(choices=("TRIAL", "PAID"), default="TRIAL")
    plan = serializers.SlugField(required=False)
    plan_slug = serializers.SlugField(required=False)
    plan_price_id = serializers.IntegerField(required=False)
    plan_price_slug = serializers.SlugField(required=False)

    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    crp = serializers.CharField(required=False, allow_blank=True)
    crp_number = serializers.CharField(required=False, allow_blank=True)
    specialty = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        prices = PlanPrice.objects.select_related("plan").filter(
            is_active=True,
            plan__is_active=True,
        )
        price = None
        if attrs.get("plan_price_id"):
            price = prices.filter(pk=attrs["plan_price_id"]).first()
        elif attrs.get("plan_price_slug"):
            price = prices.filter(slug=attrs["plan_price_slug"]).first()
        else:
            plan_slug = attrs.get("plan_slug") or attrs.get("plan")
            if plan_slug:
                price = prices.filter(plan__slug=plan_slug).order_by(
                    "billing_interval",
                    "total_amount",
                ).first()

        if not price or not price.is_available():
            raise serializers.ValidationError(
                {"plan": "Selecione um plano disponível antes de criar a conta."}
            )
        attrs["plan_price"] = price
        return attrs


class PlanRegistrationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PlanRegistrationSerializer

    @transaction.atomic
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        plan_price = data["plan_price"]

        user_payload = {
            "email": data["email"],
            "full_name": data["full_name"],
            "password": data["password"],
            "password_confirm": data["password_confirm"],
            "crp_number": data.get("crp_number") or data.get("crp", ""),
            "specialty": data.get("specialty", ""),
            "phone": data.get("phone", ""),
        }
        user_serializer = RegisterSerializer(data=user_payload)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        now = timezone.now()
        subscription = None
        if data["access_mode"] == "TRIAL":
            trial_ends_at = now + timedelta(days=TRIAL_DAYS)
            subscription = Subscription.objects.create(
                user=user,
                plan=plan_price.plan,
                status=Subscription.Status.TRIALING,
                started_at=now,
                access_starts_at=now,
                access_ends_at=trial_ends_at,
                trial_ends_at=trial_ends_at,
                metadata={
                    "trial_used": True,
                    "trial_days": TRIAL_DAYS,
                    "selected_plan_price_id": plan_price.pk,
                    "selected_plan_price_slug": plan_price.slug,
                    "registration_mode": "TRIAL",
                },
            )
            next_url = "/dashboard"
        else:
            next_url = f"/checkout?plan={plan_price.plan.slug}&price={plan_price.slug}"

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "message": "Cadastro realizado com sucesso.",
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                },
                "user": UserProfileSerializer(user).data,
                "access_mode": data["access_mode"],
                "selected_plan": PlanSerializer(plan_price.plan).data,
                "selected_plan_price": PlanPriceSerializer(plan_price).data,
                "subscription": SubscriptionSerializer(subscription).data if subscription else None,
                "next": next_url,
            },
            status=status.HTTP_201_CREATED,
        )
