from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("records", "0009_clinicalevolutiontemplate")]

    operations = [
        migrations.AddField(
            model_name="clinicalevolutiontemplate",
            name="archived_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="clinicalevolutiontemplate",
            name="category",
            field=models.CharField(blank=True, db_index=True, max_length=100),
        ),
        migrations.AddField(
            model_name="clinicalevolutiontemplate",
            name="description",
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name="clinicalevolutiontemplate",
            name="sort_order",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="clinicalevolutiontemplate",
            name="specialty",
            field=models.CharField(blank=True, db_index=True, max_length=120),
        ),
        migrations.AddField(
            model_name="clinicalevolutiontemplate",
            name="usage_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name="clinicalevolutiontemplate",
            options={
                "ordering": ["sort_order", "name"],
                "permissions": [("manage_system_clinical_templates", "Can manage system clinical evolution templates")],
            },
        ),
    ]
