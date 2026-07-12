from __future__ import annotations

import logging

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.billing.models import PlanPrice, Subscription
from apps.billing.serializers import PlanPriceSerializer, PlanSerializer, SubscriptionSerializer
from apps.billing.services.trials import start_trial
from apps.users.api.serializers import RegisterSerializer, UserProfileSerializer

logger = logging.getLogger(__name__)


class PlanRegistrationSerializer(serializers.Serializer):
    access_mode = serializers.ChoiceField(choices=("TRIAL", "PAID"), default="TRIAL")
    plan = serializers.SlugField(required=False, allow_blank=True)
    plan_slug = serializers.SlugField(required=False, allow_blank=True)
    plan_price_id = serializers.IntegerField(required=False)
    plan_price_slug = serializers.SlugField(required=False, allow_blank=True)
    billing_cycle = serializers.ChoiceField(choices=("MONTHLY", "YEARLY"), required=False)
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
                {"privacy_accepted": "É necessário aceitar a Política de Privacidade."}
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
            price = prices.filter(slug__iexact=attrs["plan_price_slug"]).first()
        else:
            plan_slug = attrs.get("plan_slug") or attrs.get("plan")
            prices = prices.filter(plan__slug__iexact=plan_slug)
            if attrs.get("billing_cycle"):
                prices = prices.filter(billing_interval=attrs["billing_cycle"])
            if attrs.get("payment_mode"):
                prices = prices.filter(billing_model=attrs["payment_mode"])
            price = prices.order_by("total_amount", "billing_model").first()

        if not price or not price.is_available():
            raise serializers.ValidationError(
                {"plan": "O plano ou a modalidade selecionada não está disponível."}
            )
        attrs["plan_price"] = price
        return attrs


def _send_account_created_email(user, *, trial_started: bool) -> None:
    subject = (
        "Seu teste gratuito no Elo Terapêutico começou"
        if trial_started
        else "Sua conta no Elo Terapêutico foi criada"
    )
    message = (
        f"Olá, {user.full_name}.\n\n"
        + (
            "Seu teste gratuito de 7 dias foi iniciado. Complete a configuração inicial para acessar o sistema."
            if trial_started
            else "Sua conta foi criada. Escolha um plano ou conclua o pagamento para liberar as ferramentas."
        )
    )
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as exc:  # pragma: no cover - falha de e-mail não desfaz cadastro
        logger.warning(
            "billing_registration_email_failed",
            extra={"user_id": user.pk, "error_type": exc.__class__.__name__},
        )


class PlanRegistrationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PlanRegistrationSerializer

    @transaction.atomic
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        plan_price = data.get("plan_price")

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

        accepted_at = timezone.now()
        user.terms_accepted_at = accepted_at
        user.privacy_accepted_at = accepted_at
        user.save(update_fields=["terms_accepted_at", "privacy_accepted_at"])

        subscription = None
        next_url = "/planos"
        if plan_price and data["access_mode"] == "TRIAL":
            try:
                subscription = start_trial(user=user, plan_price=plan_price)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    {"access_mode": list(exc.messages)}
                ) from exc
            next_url = "/onboarding"
        elif plan_price:
            subscription = Subscription.objects.create(
                user=user,
                plan=plan_price.plan,
                status=Subscription.Status.PENDING,
                metadata={
                    "selected_plan_price_id": plan_price.pk,
                    "selected_plan_price_slug": plan_price.slug,
                    "registration_mode": "PAID",
                    "awaiting_checkout": True,
                },
            )
            next_url = (
                f"/checkout?plan={plan_price.plan.slug}"
                f"&price={plan_price.slug}"
                f"&billing_cycle={plan_price.billing_interval}"
            )

        transaction.on_commit(
            lambda: _send_account_created_email(
                user,
                trial_started=bool(subscription and subscription.status == Subscription.Status.TRIALING),
            )
        )

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
                "selected_plan": PlanSerializer(plan_price.plan).data if plan_price else None,
                "selected_plan_price": PlanPriceSerializer(plan_price).data if plan_price else None,
                "subscription": SubscriptionSerializer(subscription).data if subscription else None,
                "next": next_url,
            },
            status=status.HTTP_201_CREATED,
        )
