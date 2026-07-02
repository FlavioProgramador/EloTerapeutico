# Generated for the clinical evolution modal refactor.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import core.fields


class Migration(migrations.Migration):
    dependencies = [
        ("records", "0008_alter_evolution_options"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ClinicalEvolutionTemplate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("content", core.fields.EncryptedTextField()),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="clinical_evolution_templates",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "permissions": [
                    (
                        "manage_system_clinical_templates",
                        "Can manage system clinical evolution templates",
                    )
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="clinicalevolutiontemplate",
            constraint=models.UniqueConstraint(
                fields=("owner", "name"),
                name="unique_clinical_template_owner_name",
            ),
        ),
    ]
