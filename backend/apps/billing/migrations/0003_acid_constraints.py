import django.db.models.query_utils
from django.db import migrations, models


def validate_existing_billing_data(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    Payment = apps.get_model("billing", "Payment")
    WebhookEvent = apps.get_model("billing", "WebhookEvent")

    invalid_plans = list(Plan.objects.filter(price__lt=0).values_list("pk", flat=True)[:20])
    invalid_payments = list(Payment.objects.filter(amount__lte=0).values_list("pk", flat=True)[:20])
    invalid_webhooks = list(
        WebhookEvent.objects.filter(
            django.db.models.query_utils.Q(processed=False, processed_at__isnull=False)
            | django.db.models.query_utils.Q(processed=True, processed_at__isnull=True)
        ).values_list("pk", flat=True)[:20]
    )

    problems = []
    if invalid_plans:
        problems.append(f"planos com preço negativo: {invalid_plans}")
    if invalid_payments:
        problems.append(f"pagamentos com valor não positivo: {invalid_payments}")
    if invalid_webhooks:
        problems.append(f"webhooks com timestamp inconsistente: {invalid_webhooks}")
    if problems:
        raise RuntimeError(
            "Não foi possível aplicar as constraints ACID de billing; corrija antes: "
            + "; ".join(problems)
        )


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0002_seed_initial_plans"),
    ]

    operations = [
        migrations.RunPython(validate_existing_billing_data, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="plan",
            constraint=models.CheckConstraint(
                condition=django.db.models.query_utils.Q(("price__gte", 0)),
                name="billing_plan_price_non_negative",
            ),
        ),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.CheckConstraint(
                condition=django.db.models.query_utils.Q(("amount__gt", 0)),
                name="billing_payment_amount_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="webhookevent",
            constraint=models.CheckConstraint(
                condition=(
                    django.db.models.query_utils.Q(("processed", False), ("processed_at__isnull", True))
                    | django.db.models.query_utils.Q(("processed", True), ("processed_at__isnull", False))
                ),
                name="billing_webhook_processed_timestamp_consistent",
            ),
        ),
    ]
