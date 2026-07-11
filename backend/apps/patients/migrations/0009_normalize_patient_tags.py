from django.db import migrations, models


def normalize_patient_tags(apps, schema_editor):
    Patient = apps.get_model("patients", "Patient")
    Patient._base_manager.filter(tags__isnull=True).update(tags=[])


class Migration(migrations.Migration):
    dependencies = [
        ("patients", "0008_sync_patient_relationship_labels"),
    ]

    operations = [
        migrations.RunPython(normalize_patient_tags, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="patient",
            name="tags",
            field=models.JSONField(blank=True, default=list, verbose_name="Etiquetas"),
        ),
    ]
