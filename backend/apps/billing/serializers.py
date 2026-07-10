import re

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from apps.billing.models import Payment, Plan, Subscription
from core.validators import validate_cpf as validate_cpf_value


def _validate_cnpj(value: str) -> None:
    if len(value) != 14 or value == value[0] * 14:
        raise serializers.ValidationError("CNPJ invalido.")

    first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    first_sum = sum(int(value[index]) * weight for index, weight in enumerate(first_weights))
    first_digit = 0 if first_sum % 11 < 2 else 11 - (first_sum % 11)

    second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    second_sum = sum(int(value[index]) * weight for index, weight in enumerate(second_weights))
    second_digit = 0 if second_sum % 11 < 2 else 11 - (second_sum % 11)

    if first_digit != int(value[12]) or second_digit != int(value[13]):
        raise serializers.ValidationError("CNPJ invalido.")


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


class CheckoutSerializer(serializers.Serializer):
    CHECKOUT_TYPES = ("SUBSCRIPTION", "ONE_TIME")
    BILLING_TYPES = ("PIX", "BOLETO", "CREDIT_CARD")

    plan_id = serializers.IntegerField(required=False)
    plan_slug = serializers.SlugField(required=False)
    type = serializers.ChoiceField(choices=CHECKOUT_TYPES, default="SUBSCRIPTION")
    billingType = serializers.ChoiceField(choices=BILLING_TYPES, default="PIX")
    cpfCnpj = serializers.CharField(write_only=True, trim_whitespace=True)
    dueDate = serializers.DateField()
    value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    cycle = serializers.ChoiceField(choices=("MONTHLY", "YEARLY"), required=False)
    installmentCount = serializers.IntegerField(min_value=1, max_value=12, required=False, default=1)
    creditCardToken = serializers.CharField(required=False, write_only=True, trim_whitespace=True)

    def validate_dueDate(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("O vencimento não pode ser anterior à data atual.")
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
            raise serializers.ValidationError("Informe CPF ou CNPJ com 11 ou 14 digitos.")
        return clean_value

    def validate(self, attrs):
        plan_id = attrs.get("plan_id")
        plan_slug = attrs.get("plan_slug")
        if not plan_id and not plan_slug:
            raise serializers.ValidationError("Informe plan_id ou plan_slug para o checkout.")

        queryset = Plan.objects.filter(is_active=True)
        try:
            plan = queryset.get(pk=plan_id) if plan_id else queryset.get(slug=plan_slug)
        except Plan.DoesNotExist as exc:
            raise serializers.ValidationError("Plano não encontrado ou indisponível.") from exc

        attrs["plan"] = plan
        attrs["value"] = plan.price
        attrs["cycle"] = attrs.get("cycle") or plan.billing_cycle
        attrs["description"] = attrs.get("description") or f"Assinatura Elo Terapêutico - {plan.name}"

        if attrs["type"] == "SUBSCRIPTION" and int(attrs.get("installmentCount") or 1) > 1:
            raise serializers.ValidationError({"installmentCount": "Parcelamento só é permitido para cobrança única."})

        if attrs["billingType"] == "CREDIT_CARD" and not attrs.get("creditCardToken"):
            raise serializers.ValidationError(
                {"billingType": "Cartão de crédito será habilitado apenas via checkout/tokenização segura futura."}
            )

        return attrs


class CheckoutPreviewSerializer(CheckoutSerializer):
    pass


class CheckoutCreateSerializer(CheckoutSerializer):
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
            "gateway_payment_id",
            "gateway_subscription_id",
            "invoice_url",
            "bank_slip_url",
            "pix_qr_code",
            "pix_copy_paste",
            "created_at",
        ]
