import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


OPERATIONAL_STATUSES = ["TRIALING", "PENDING", "ACTIVE", "PAST_DUE", "SUSPENDED"]


def migrate_legacy_billing(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    PlanPrice = apps.get_model("billing", "PlanPrice")
    BillingOrder = apps.get_model("billing", "BillingOrder")
    Subscription = apps.get_model("billing", "Subscription")
    Payment = apps.get_model("billing", "Payment")

    price_by_plan = {}
    for plan in Plan.objects.all().iterator():
        interval = "YEARLY" if plan.billing_cycle == "YEARLY" else "MONTHLY"
        price, _ = PlanPrice.objects.get_or_create(
            slug=f"{plan.slug}-{interval.lower()}-legacy",
            defaults={
                "plan_id": plan.pk,
                "name": f"{plan.name} — {'Anual' if interval == 'YEARLY' else 'Mensal'}",
                "currency": plan.currency,
                "total_amount": plan.price,
                "billing_interval": interval,
                "billing_model": "RECURRING",
                "discount_percentage": Decimal("0.00"),
                "installments_enabled": False,
                "min_installments": 1,
                "max_installments": 1,
                "trial_days": 0,
                "is_active": plan.is_active,
            },
        )
        price_by_plan[plan.pk] = price

    for subscription in Subscription.objects.select_related("plan").all().iterator():
        price = price_by_plan.get(subscription.plan_id)
        if not price:
            continue
        order, _ = BillingOrder.objects.get_or_create(
            external_reference=f"legacy-subscription-{subscription.pk}",
            defaults={
                "public_id": uuid.uuid4(),
                "user_id": subscription.user_id,
                "plan_id": subscription.plan_id,
                "plan_price_id": price.pk,
                "status": "PAID" if subscription.status == "ACTIVE" else "PENDING",
                "billing_model": price.billing_model,
                "billing_interval": price.billing_interval,
                "currency": price.currency,
                "total_amount": price.total_amount,
                "discount_amount": Decimal("0.00"),
                "installment_count": 1,
                "installment_amount_estimate": price.total_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "gateway_name": subscription.gateway_name,
                "gateway_customer_id": subscription.gateway_customer_id,
                "gateway_subscription_id": subscription.gateway_subscription_id,
                "gateway_installment_id": "",
                "idempotency_key": f"legacy-subscription-{subscription.pk}",
                "commercial_snapshot": {
                    "legacy": True,
                    "plan_name": subscription.plan.name,
                    "amount": str(price.total_amount),
                    "currency": price.currency,
                },
                "metadata": {"migrated_from_subscription_id": subscription.pk},
                "confirmed_at": subscription.started_at if subscription.status == "ACTIVE" else None,
            },
        )
        subscription.billing_order_id = order.pk
        subscription.access_starts_at = subscription.current_period_start or subscription.started_at
        subscription.access_ends_at = subscription.current_period_end
        subscription.save(update_fields=["billing_order", "access_starts_at", "access_ends_at"])
        Payment.objects.filter(subscription_id=subscription.pk, billing_order__isnull=True).update(
            billing_order_id=order.pk
        )

    # A constraint parcial exige apenas uma assinatura operacional por usuário.
    # Mantém a mais recente e encerra registros antigos sem apagar histórico.
    user_ids = (
        Subscription.objects.filter(status__in=OPERATIONAL_STATUSES)
        .values_list("user_id", flat=True)
        .distinct()
    )
    for user_id in user_ids.iterator():
        subscriptions = list(
            Subscription.objects.filter(user_id=user_id, status__in=OPERATIONAL_STATUSES)
            .order_by("-created_at", "-pk")
        )
        for duplicate in subscriptions[1:]:
            duplicate.status = "CANCELED"
            duplicate.canceled_at = duplicate.updated_at or duplicate.created_at
            duplicate.save(update_fields=["status", "canceled_at"])


def reverse_legacy_billing(apps, schema_editor):
    BillingOrder = apps.get_model("billing", "BillingOrder")
    PlanPrice = apps.get_model("billing", "PlanPrice")
    Subscription = apps.get_model("billing", "Subscription")
    Payment = apps.get_model("billing", "Payment")

    legacy_orders = BillingOrder.objects.filter(external_reference__startswith="legacy-subscription-")
    legacy_order_ids = list(legacy_orders.values_list("pk", flat=True))
    Subscription.objects.filter(billing_order_id__in=legacy_order_ids).update(
        billing_order=None,
        access_starts_at=None,
        access_ends_at=None,
    )
    Payment.objects.filter(billing_order_id__in=legacy_order_ids).update(billing_order=None)
    legacy_orders.delete()
    PlanPrice.objects.filter(slug__endswith="-legacy").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0003_acid_constraints"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="plan",
            options={"ordering": ["name"], "verbose_name": "Plano", "verbose_name_plural": "Planos"},
        ),
        migrations.AlterField(
            model_name="plan",
            name="price",
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Preço legado"),
        ),
        migrations.AlterField(
            model_name="plan",
            name="currency",
            field=models.CharField(default="BRL", max_length=3, verbose_name="Moeda legada"),
        ),
        migrations.AlterField(
            model_name="plan",
            name="billing_cycle",
            field=models.CharField(
                choices=[("MONTHLY", "Mensal"), ("YEARLY", "Anual")],
                default="MONTHLY",
                max_length=20,
                verbose_name="Ciclo legado",
            ),
        ),
        migrations.CreateModel(
            name="PlanPrice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(unique=True)),
                ("currency", models.CharField(default="BRL", max_length=3)),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("billing_interval", models.CharField(choices=[("MONTHLY", "Mensal"), ("YEARLY", "Anual")], max_length=20)),
                ("billing_model", models.CharField(choices=[("RECURRING", "Recorrente"), ("ONE_TIME", "À vista"), ("INSTALLMENT", "Parcelado")], max_length=20)),
                ("discount_percentage", models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ("installments_enabled", models.BooleanField(default=False)),
                ("min_installments", models.PositiveSmallIntegerField(default=1)),
                ("max_installments", models.PositiveSmallIntegerField(default=1)),
                ("trial_days", models.PositiveSmallIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("starts_at", models.DateTimeField(blank=True, null=True)),
                ("ends_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="prices", to="billing.plan")),
            ],
            options={"verbose_name": "Preço do plano", "verbose_name_plural": "Preços dos planos", "ordering": ["plan__name", "billing_interval", "total_amount"]},
        ),
        migrations.CreateModel(
            name="BillingOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("status", models.CharField(choices=[("DRAFT", "Rascunho"), ("PENDING", "Pendente"), ("PARTIALLY_PAID", "Parcialmente pago"), ("PAID", "Pago"), ("OVERDUE", "Em atraso"), ("CANCELED", "Cancelado"), ("REFUNDED", "Estornado"), ("PARTIALLY_REFUNDED", "Parcialmente estornado"), ("CHARGEBACK", "Chargeback"), ("FAILED", "Falhou"), ("EXPIRED", "Expirado")], db_index=True, default="DRAFT", max_length=30)),
                ("billing_model", models.CharField(choices=[("RECURRING", "Recorrente"), ("ONE_TIME", "À vista"), ("INSTALLMENT", "Parcelado")], max_length=20)),
                ("billing_interval", models.CharField(choices=[("MONTHLY", "Mensal"), ("YEARLY", "Anual")], max_length=20)),
                ("currency", models.CharField(default="BRL", max_length=3)),
                ("total_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("discount_amount", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("installment_count", models.PositiveSmallIntegerField(default=1)),
                ("installment_amount_estimate", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("gateway_name", models.CharField(default="ASAAS", max_length=40)),
                ("gateway_customer_id", models.CharField(blank=True, max_length=120)),
                ("gateway_subscription_id", models.CharField(blank=True, db_index=True, max_length=120)),
                ("gateway_installment_id", models.CharField(blank=True, db_index=True, max_length=120)),
                ("external_reference", models.CharField(max_length=160, unique=True)),
                ("idempotency_key", models.CharField(max_length=160, unique=True)),
                ("commercial_snapshot", models.JSONField(blank=True, default=dict)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("canceled_at", models.DateTimeField(blank=True, null=True)),
                ("failed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="billing_orders", to="billing.plan")),
                ("plan_price", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="billing_orders", to="billing.planprice")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="billing_orders", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Contratação", "verbose_name_plural": "Contratações", "ordering": ["-created_at"]},
        ),
        migrations.AddField(model_name="subscription", name="billing_order", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="subscriptions", to="billing.billingorder")),
        migrations.AddField(model_name="subscription", name="access_starts_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="subscription", name="access_ends_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="subscription", name="grace_period_ends_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="subscription", name="cancel_at_period_end", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="subscription", name="suspended_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="subscription", name="reactivated_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AlterField(model_name="subscription", name="status", field=models.CharField(choices=[("TRIALING", "Em teste"), ("PENDING", "Pendente"), ("ACTIVE", "Ativa"), ("PAST_DUE", "Em atraso"), ("SUSPENDED", "Suspensa"), ("CANCELED", "Cancelada"), ("EXPIRED", "Expirada")], db_index=True, default="PENDING", max_length=20)),
        migrations.AlterModelOptions(name="payment", options={"ordering": ["due_date", "installment_number", "created_at"], "verbose_name": "Pagamento", "verbose_name_plural": "Pagamentos"}),
        migrations.AddField(model_name="payment", name="billing_order", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="payments", to="billing.billingorder")),
        migrations.AlterField(model_name="payment", name="subscription", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="payments", to="billing.subscription")),
        migrations.AddField(model_name="payment", name="net_amount", field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
        migrations.AddField(model_name="payment", name="interest_amount", field=models.DecimalField(decimal_places=2, default=0, max_digits=10)),
        migrations.AddField(model_name="payment", name="fine_amount", field=models.DecimalField(decimal_places=2, default=0, max_digits=10)),
        migrations.AddField(model_name="payment", name="discount_amount", field=models.DecimalField(decimal_places=2, default=0, max_digits=10)),
        migrations.AddField(model_name="payment", name="billing_type", field=models.CharField(choices=[("PIX", "Pix"), ("BOLETO", "Boleto"), ("CREDIT_CARD", "Cartão de crédito"), ("UNDEFINED", "Não definido")], default="UNDEFINED", max_length=20)),
        migrations.AlterField(model_name="payment", name="status", field=models.CharField(choices=[("PENDING", "Pendente"), ("AUTHORIZED", "Autorizado"), ("CONFIRMED", "Confirmado"), ("RECEIVED", "Recebido"), ("OVERDUE", "Vencido"), ("FAILED", "Falhou"), ("CANCELED", "Cancelado"), ("REFUNDED", "Estornado"), ("PARTIALLY_REFUNDED", "Parcialmente estornado"), ("REFUND_IN_PROGRESS", "Estorno em andamento"), ("CHARGEBACK", "Chargeback"), ("CHARGEBACK_DISPUTE", "Disputa de chargeback"), ("RESTORED", "Restaurado"), ("AWAITING_RISK_ANALYSIS", "Em análise de risco")], db_index=True, default="PENDING", max_length=30)),
        migrations.AddField(model_name="payment", name="original_due_date", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="payment", name="confirmed_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="payment", name="credit_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="payment", name="refunded_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="payment", name="gateway_installment_id", field=models.CharField(blank=True, db_index=True, max_length=120)),
        migrations.AddField(model_name="payment", name="installment_number", field=models.PositiveSmallIntegerField(blank=True, null=True)),
        migrations.AddField(model_name="payment", name="installment_count", field=models.PositiveSmallIntegerField(default=1)),
        migrations.AddField(model_name="payment", name="invoice_number", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name="payment", name="transaction_receipt_url", field=models.URLField(blank=True)),
        migrations.AddField(model_name="payment", name="external_reference", field=models.CharField(blank=True, db_index=True, max_length=160)),
        migrations.AddField(model_name="webhookevent", name="status", field=models.CharField(choices=[("RECEIVED", "Recebido"), ("PROCESSING", "Processando"), ("PROCESSED", "Processado"), ("RETRY", "Aguardando nova tentativa"), ("FAILED", "Falhou"), ("IGNORED", "Ignorado")], db_index=True, default="RECEIVED", max_length=20)),
        migrations.AddField(model_name="webhookevent", name="attempt_count", field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name="webhookevent", name="next_retry_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="webhookevent", name="last_error", field=models.TextField(blank=True)),
        migrations.AddField(model_name="webhookevent", name="updated_at", field=models.DateTimeField(auto_now=True)),
        migrations.RunPython(migrate_legacy_billing, reverse_legacy_billing),
        migrations.AddConstraint(model_name="planprice", constraint=models.CheckConstraint(condition=models.Q(("total_amount__gt", 0)), name="billing_price_amount_positive")),
        migrations.AddConstraint(model_name="planprice", constraint=models.CheckConstraint(condition=models.Q(("discount_percentage__gte", 0), ("discount_percentage__lte", 100)), name="billing_price_discount_range")),
        migrations.AddConstraint(model_name="planprice", constraint=models.CheckConstraint(condition=models.Q(("min_installments__gte", 1), ("max_installments__gte", models.F("min_installments"))), name="billing_price_installment_range")),
        migrations.AddIndex(model_name="planprice", index=models.Index(fields=["plan", "is_active"], name="billing_price_plan_active_idx")),
        migrations.AddIndex(model_name="planprice", index=models.Index(fields=["billing_interval", "billing_model"], name="billing_price_mode_idx")),
        migrations.AddConstraint(model_name="billingorder", constraint=models.CheckConstraint(condition=models.Q(("total_amount__gt", 0)), name="billing_order_amount_positive")),
        migrations.AddConstraint(model_name="billingorder", constraint=models.CheckConstraint(condition=models.Q(("installment_count__gte", 1)), name="billing_order_installment_positive")),
        migrations.AddIndex(model_name="billingorder", index=models.Index(fields=["user", "status"], name="billing_order_user_status_idx")),
        migrations.AddIndex(model_name="billingorder", index=models.Index(fields=["gateway_installment_id"], name="billing_order_installment_idx")),
        migrations.AddConstraint(model_name="subscription", constraint=models.UniqueConstraint(condition=models.Q(("status__in", OPERATIONAL_STATUSES)), fields=("user",), name="billing_one_operational_subscription")),
        migrations.AddConstraint(model_name="payment", constraint=models.CheckConstraint(condition=models.Q(("installment_count__gte", 1)), name="billing_payment_installment_positive")),
        migrations.AddConstraint(model_name="payment", constraint=models.UniqueConstraint(condition=models.Q(("billing_order__isnull", False), ("installment_number__isnull", False)), fields=("billing_order", "installment_number"), name="billing_unique_order_installment")),
        migrations.AddIndex(model_name="payment", index=models.Index(fields=["gateway_installment_id"], name="billing_pay_installment_idx")),
        migrations.AddIndex(model_name="payment", index=models.Index(fields=["billing_order", "installment_number"], name="billing_pay_order_number_idx")),
        migrations.AddIndex(model_name="webhookevent", index=models.Index(fields=["status", "next_retry_at"], name="billing_webhook_retry_idx")),
    ]
