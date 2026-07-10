import django.db.models.query_utils
from django.db import migrations, models


def classify_existing_appointment_entries(apps, schema_editor):
    FinancialTransaction = apps.get_model("financeiro", "FinancialTransaction")
    candidates = (
        FinancialTransaction.objects.filter(
            appointment__isnull=False,
            source="manual",
            category="session",
            transaction_type="income",
            description__startswith="Consulta de ",
        )
        .order_by("appointment_id", "created_at", "pk")
        .only("pk", "appointment_id", "source")
    )

    classified_appointments = set()
    for item in candidates.iterator():
        if item.appointment_id in classified_appointments:
            continue
        item.source = "appointment"
        item.save(update_fields=["source"])
        classified_appointments.add(item.appointment_id)


def restore_manual_source(apps, schema_editor):
    FinancialTransaction = apps.get_model("financeiro", "FinancialTransaction")
    FinancialTransaction.objects.filter(source="appointment").update(source="manual")


class Migration(migrations.Migration):
    dependencies = [
        ("financeiro", "0010_align_transaction_labels"),
    ]

    operations = [
        migrations.RunPython(
            classify_existing_appointment_entries,
            restore_manual_source,
        ),
        migrations.AddConstraint(
            model_name="financialtransaction",
            constraint=models.UniqueConstraint(
                condition=django.db.models.query_utils.Q(
                    ("appointment__isnull", False),
                    ("source", "appointment"),
                ),
                fields=("appointment",),
                name="fin_unique_appointment_source",
            ),
        ),
    ]
