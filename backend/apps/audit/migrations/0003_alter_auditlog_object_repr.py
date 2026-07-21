from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0002_audit_organization"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="object_repr",
            field=models.CharField(
                blank=True,
                max_length=200,
                verbose_name="Representação do objeto",
            ),
        ),
    ]
