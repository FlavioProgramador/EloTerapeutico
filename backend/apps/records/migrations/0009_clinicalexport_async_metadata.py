import uuid

from django.db import migrations, models
from django.db.models import Q


def populate_public_ids(apps, schema_editor):
    ClinicalExport = apps.get_model("records", "ClinicalExport")
    for export_obj in ClinicalExport.objects.filter(public_id__isnull=True).iterator(chunk_size=500):
        export_obj.public_id = uuid.uuid4()
        export_obj.save(update_fields=["public_id"])


class Migration(migrations.Migration):
    dependencies = [
        ("records", "0008_alter_evolution_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="clinicalexport",
            name="public_id",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.RunPython(populate_public_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="clinicalexport",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name="clinicalexport",
            name="content_type",
            field=models.CharField(default="application/pdf", max_length=120),
        ),
        migrations.AddField(
            model_name="clinicalexport",
            name="checksum_sha256",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="clinicalexport",
            name="progress",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="clinicalexport",
            name="expires_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="clinicalexport",
            name="error_code",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="clinicalexport",
            name="metadata",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name="clinicalexport",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pendente"),
                    ("PROCESSING", "Processando"),
                    ("COMPLETED", "Concluído"),
                    ("FAILED", "Falhou"),
                    ("EXPIRED", "Expirado"),
                    ("CANCELLED", "Cancelado"),
                ],
                default="PENDING",
                max_length=50,
                verbose_name="Status",
            ),
        ),
        migrations.AddIndex(
            model_name="clinicalexport",
            index=models.Index(fields=["status", "created_at"], name="export_status_created_idx"),
        ),
        migrations.AddConstraint(
            model_name="clinicalexport",
            constraint=models.CheckConstraint(
                condition=Q(progress__gte=0, progress__lte=100),
                name="export_progress_valid",
            ),
        ),
    ]
