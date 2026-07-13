import django.db.models.deletion
from django.db import migrations, models


def seed_entitlements(apps, schema_editor):
    Plan = apps.get_model("billing", "Plan")
    Entitlement = apps.get_model("communications", "CommunicationPlanEntitlement")
    for plan in Plan.objects.all().iterator():
        slug = (plan.slug or "").lower()
        is_entry = any(token in slug for token in ("basic", "starter", "essencial", "free"))
        Entitlement.objects.get_or_create(
            plan=plan,
            defaults={
                "communications_enabled": True,
                "email_enabled": True,
                "custom_templates_enabled": not is_entry,
                "automations_enabled": not is_entry,
                "advanced_automations_enabled": False,
                "whatsapp_enabled": False,
                "sms_enabled": False,
                "metrics_enabled": True,
                "max_communications_per_month": 200 if is_entry else 1000,
                "max_email_communications_per_month": 200 if is_entry else 1000,
                "max_automations": 0 if is_entry else 20,
                "max_custom_templates": 0 if is_entry else 50,
            },
        )


def unseed_entitlements(apps, schema_editor):
    apps.get_model("communications", "CommunicationPlanEntitlement").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("communications", "0006_seed_default_templates"),
        ("billing", "0004_professional_billing_domain"),
    ]
    operations = [
        migrations.CreateModel(
            name="CommunicationPlanEntitlement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("communications_enabled", models.BooleanField(default=True)),
                ("email_enabled", models.BooleanField(default=True)),
                ("custom_templates_enabled", models.BooleanField(default=True)),
                ("automations_enabled", models.BooleanField(default=True)),
                ("advanced_automations_enabled", models.BooleanField(default=False)),
                ("whatsapp_enabled", models.BooleanField(default=False)),
                ("sms_enabled", models.BooleanField(default=False)),
                ("metrics_enabled", models.BooleanField(default=True)),
                ("max_communications_per_month", models.PositiveIntegerField(blank=True, default=500, null=True)),
                ("max_email_communications_per_month", models.PositiveIntegerField(blank=True, default=500, null=True)),
                ("max_automations", models.PositiveIntegerField(blank=True, default=10, null=True)),
                ("max_custom_templates", models.PositiveIntegerField(blank=True, default=20, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("plan", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="communication_entitlement", to="billing.plan")),
            ],
            options={"verbose_name": "Recurso de comunicações por plano", "verbose_name_plural": "Recursos de comunicações por plano"},
        ),
        migrations.RunPython(seed_entitlements, unseed_entitlements),
    ]
