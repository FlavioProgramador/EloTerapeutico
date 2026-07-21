import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0003_organization_tenant"),
    ]

    operations = [
        migrations.AlterField(
            model_name="documenttemplate",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                help_text="Nulo somente para templates globais da biblioteca.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="document_templates",
                to="organizations.organization",
            ),
        ),
    ]
