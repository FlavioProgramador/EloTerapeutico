import apps.records.treatment_models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("records", "0011_clinicalexport_async_metadata"),
    ]

    operations = [
        migrations.AlterField(
            model_name="clinicaldocument",
            name="file",
            field=models.FileField(
                blank=True,
                help_text="Arquivo liberado após análise antimalware.",
                null=True,
                upload_to=apps.records.treatment_models.clinical_document_path,
            ),
        ),
        migrations.AddField(
            model_name="clinicaldocument",
            name="quarantine_file",
            field=models.FileField(
                blank=True,
                help_text="Arquivo temporário, indisponível para download até a análise.",
                null=True,
                upload_to=apps.records.treatment_models.clinical_document_quarantine_path,
            ),
        ),
        migrations.AddField(
            model_name="clinicaldocument",
            name="scan_status",
            field=models.CharField(
                choices=[
                    ("pending", "Aguardando análise"),
                    ("scanning", "Em análise"),
                    ("clean", "Liberado"),
                    ("infected", "Arquivo rejeitado"),
                    ("failed", "Falha na análise"),
                ],
                db_index=True,
                default="clean",
                max_length=16,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="clinicaldocument",
            name="scan_attempts",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="clinicaldocument",
            name="scan_error_code",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="clinicaldocument",
            name="scan_started_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="clinicaldocument",
            name="scanned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="clinicaldocument",
            name="scan_status",
            field=models.CharField(
                choices=[
                    ("pending", "Aguardando análise"),
                    ("scanning", "Em análise"),
                    ("clean", "Liberado"),
                    ("infected", "Arquivo rejeitado"),
                    ("failed", "Falha na análise"),
                ],
                db_index=True,
                default="pending",
                max_length=16,
            ),
        ),
        migrations.AddIndex(
            model_name="clinicaldocument",
            index=models.Index(
                fields=["scan_status", "scan_started_at"],
                name="document_scan_status_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="clinicaldocument",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(file__isnull=False, scan_status="clean")
                    | ~models.Q(scan_status="clean")
                ),
                name="clinical_document_clean_has_file",
            ),
        ),
    ]
