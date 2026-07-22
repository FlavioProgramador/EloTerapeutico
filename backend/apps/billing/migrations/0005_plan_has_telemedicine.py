from django.db import migrations, models


def enable_telemedicine_for_eligible_plans(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    Plan.objects.filter(slug__in=["profissional", "premium"]).update(
        has_telemedicine=True
    )


def disable_telemedicine(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    Plan.objects.update(has_telemedicine=False)


class Migration(migrations.Migration):
    dependencies = [("billing", "0004_professional_billing_domain")]

    operations = [
        migrations.AddField(
            model_name="plan",
            name="has_telemedicine",
            field=models.BooleanField(default=False, verbose_name="Telemedicina"),
        ),
        migrations.RunPython(
            enable_telemedicine_for_eligible_plans,
            reverse_code=disable_telemedicine,
        ),
    ]
