from __future__ import annotations

import re
import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from apps.billing.models import Plan, PlanPrice
from apps.billing.services.orders import preview_order
from apps.core.validators import validate_cpf as validate_cpf_value


def _validate_cnpj(value: str) -> None:
    if len(value) != 14 or value == value[0] * 14:
        raise serializers.ValidationError("CNPJ inválido.")
    first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    first_sum = sum(
        int(value[index]) * weight
        for index, weight in enumerate(first_weights)
    )
    first_digit = 0 if first_sum % 11 < 2 else 11 - (first_sum % 11)
    second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    second_sum = sum(
        int(value[index]) * weight
        for index, weight in enumerate(second_weights)
    )
    second_digit = 0 if second_sum % 11 < 2 else 11 - (second_sum % 11)
    if first_digit != int(value[12]) or second_digit != int(value[13]):
        raise serializers.ValidationError("CNPJ inválido.")


class CheckoutSerializer(serializers.Serializer):
    BILLING_TYPES = ("PIX", "BOLETO", "CREDIT_CARD")
    LEGACY_TYPES = ("SUBSCRIPTION", "ONE_TIME")

    plan_price_id = serializers.IntegerField(required=False)
    plan_price_slug = serializers.SlugField(required=False)
    plan_id = serializers.IntegerField(
        required=False,
        help_text="Compatibilidade temporária",
    )
    plan_slug = serializers.SlugField(
        required=False,
        help_text="Compatibilidade temporária",
    )
    type = serializers.ChoiceField(
        choices=LEGACY_TYPES,
        required=False,
        write_only=True,
    )
    value = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        write_only=True,
    )
    cycle = serializers.ChoiceField(
        choices=("MONTHLY", "YEARLY"),
        required=False,
        write_only=True,
    )
    billingType = serializers.ChoiceField(choices=BILLING_TYPES, default="PIX")
    cpfCnpj = serializers.CharField(write_only=True, trim_whitespace=True)
    name = serializers.CharField(max_length=160, required=False, allow_blank=True)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    dueDate = serializers.DateField()
    description = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
    )
    installmentCount = serializers.IntegerField(
        min_value=1,
        max_value=12,
        required=False,
        default=1,
    )
    creditCardToken = serializers.CharField(
        required=False,
        write_only=True,
        trim_whitespace=True,
    )
    idempotency_key = serializers.CharField(
        max_length=160,
        required=False,
        write_only=True,
    )

    def validate_dueDate(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError(
                "O vencimento não pode ser anterior à data atual."
            )
        return value

    def validate_cpfCnpj(self, value):
        clean_value = re.sub(r"\D", "", value or "")
        if len(clean_value) == 11:
            try:
                validate_cpf_value(clean_value)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.messages[0]) from exc
        elif len(clean_value) == 14:
            _validate_cnpj(clean_value)
        else:
            raise serializers.ValidationError(
                "Informe CPF ou CNPJ com 11 ou 14 dígitos."
            )
        return clean_value

    @staticmethod
    def _legacy_billing_model(attrs) -> str:
        if attrs.get("type") == "ONE_TIME":
            return (
                PlanPrice.BillingModel.INSTALLMENT
                if int(attrs.get("installmentCount") or 1) > 1
                else PlanPrice.BillingModel.ONE_TIME
            )
        return PlanPrice.BillingModel.RECURRING

    def _legacy_price(self, plan: Plan, attrs) -> PlanPrice:
        interval = attrs.get("cycle") or plan.billing_cycle
        model = self._legacy_billing_model(attrs)
        installment_count = int(attrs.get("installmentCount") or 1)
        slug = f"{plan.slug}-{interval.lower()}-{model.lower()}-legacy"
        price, _ = PlanPrice.objects.get_or_create(
            slug=slug,
            defaults={
                "plan": plan,
                "name": (
                    f"{plan.name} — "
                    f"{'Anual' if interval == 'YEARLY' else 'Mensal'}"
                ),
                "currency": plan.currency,
                "total_amount": plan.price,
                "billing_interval": interval,
                "billing_model": model,
                "discount_percentage": Decimal("0.00"),
                "installments_enabled": (
                    model == PlanPrice.BillingModel.INSTALLMENT
                ),
                "min_installments": (
                    2 if model == PlanPrice.BillingModel.INSTALLMENT else 1
                ),
                "max_installments": (
                    max(installment_count, 12)
                    if model == PlanPrice.BillingModel.INSTALLMENT
                    else 1
                ),
                "trial_days": 0,
                "is_active": plan.is_active,
            },
        )
        return price

    def _resolve_plan_price(self, attrs):
        price_id = attrs.get("plan_price_id")
        price_slug = attrs.get("plan_price_slug")
        queryset = PlanPrice.objects.select_related("plan").filter(
            is_active=True,
            plan__is_active=True,
        )
        try:
            if price_id:
                return queryset.get(pk=price_id)
            if price_slug:
                return queryset.get(slug=price_slug)
        except PlanPrice.DoesNotExist as exc:
            raise serializers.ValidationError(
                "Preço do plano não encontrado ou indisponível."
            ) from exc

        plan_id = attrs.get("plan_id")
        plan_slug = attrs.get("plan_slug")
        if not plan_id and not plan_slug:
            raise serializers.ValidationError(
                "Informe plan_price_id ou plan_price_slug."
            )
        plans = Plan.objects.filter(is_active=True)
        try:
            plan = plans.get(pk=plan_id) if plan_id else plans.get(slug=plan_slug)
        except Plan.DoesNotExist as exc:
            raise serializers.ValidationError(
                "Plano não encontrado ou indisponível."
            ) from exc

        desired_model = self._legacy_billing_model(attrs)
        price = (
            queryset.filter(plan=plan, billing_model=desired_model)
            .order_by("billing_interval", "total_amount")
            .first()
        )
        return price or self._legacy_price(plan, attrs)

    def validate(self, attrs):
        plan_price = self._resolve_plan_price(attrs)
        attrs["plan_price"] = plan_price
        attrs["plan"] = plan_price.plan
        attrs["description"] = attrs.get("description") or (
            f"Elo Terapêutico — {plan_price.name}"
        )
        try:
            attrs["preview"] = preview_order(
                plan_price,
                attrs.get("installmentCount", 1),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages[0]) from exc
        if attrs["billingType"] == "CREDIT_CARD" and not attrs.get(
            "creditCardToken"
        ):
            raise serializers.ValidationError(
                {
                    "billingType": (
                        "Cartão exige tokenização segura ou checkout hospedado "
                        "do Asaas."
                    )
                }
            )
        return attrs


class CheckoutPreviewSerializer(CheckoutSerializer):
    pass


class CheckoutCreateSerializer(CheckoutSerializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get("idempotency_key"):
            request = self.context.get("request")
            attrs["idempotency_key"] = (
                request.headers.get("Idempotency-Key") if request else None
            )
        if not attrs.get("idempotency_key") and (
            attrs.get("plan_id") or attrs.get("plan_slug")
        ):
            attrs["idempotency_key"] = f"legacy-{uuid.uuid4()}"
        if (
            not attrs.get("idempotency_key")
            or len(attrs["idempotency_key"]) < 8
        ):
            raise serializers.ValidationError(
                {
                    "idempotency_key": (
                        "Informe uma chave de idempotência válida."
                    )
                }
            )
        return attrs
