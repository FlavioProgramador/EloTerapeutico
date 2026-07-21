import django.db.models.deletion
from django.db import migrations, models


MODEL_NAMES = (
    "Evolution",
    "Anamnesis",
    "TreatmentGoal",
    "ClinicalDocument",
    "ClinicalExport",
    "ClinicalFormResponse",
)


def backfill_record_organizations(apps, schema_editor):
    for model_name in MODEL_NAMES:
        model = apps.get_model("records", model_name)
        rows = model.objects.filter(
            organization__isnull=True,
            patient__organization__isnull=False,
        ).values_list("pk", "patient__organization_id")
        for object_id, organization_id in rows.iterator(chunk_size=500):
            model.objects.filter(pk=object_id, organization__isnull=True).update(
                organization_id=organization_id
            )


def assert_no_missing_tenant(apps, schema_editor):
    for model_name in MODEL_NAMES:
        model = apps.get_model("records", model_name)
        missing = model.objects.filter(organization__isnull=True).count()
        if missing:
            raise RuntimeError(
                f"Existem {missing} registro(s) de {model_name} sem organização. "
                "Execute backfill_organizations antes de continuar."
            )


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0001_initial"),
        ("patients", "0010_patient_organization"),
        ("records", "0012_clinicaldocument_quarantine_scan"),
    ]

    operations = [
        *[
            migrations.AddField(
                model_name=model_name.lower(),
                name="organization",
                field=models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name=f"records_{model_name.lower()}_items",
                    to="organizations.organization",
                ),
            )
            for model_name in MODEL_NAMES
        ],
        migrations.RunPython(backfill_record_organizations, migrations.RunPython.noop),
        migrations.RunPython(assert_no_missing_tenant, migrations.RunPython.noop),
        *[
            migrations.AlterField(
                model_name=model_name.lower(),
                name="organization",
                field=models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name=f"records_{model_name.lower()}_items",
                    to="organizations.organization",
                ),
            )
            for model_name in MODEL_NAMES
        ],
        migrations.AddIndex(
            model_name="evolution",
            index=models.Index(fields=["organization", "patient", "session_date"], name="evolution_org_patient_idx"),
        ),
        migrations.AddIndex(
            model_name="anamnesis",
            index=models.Index(fields=["organization", "patient"], name="anamnesis_org_patient_idx"),
        ),
        migrations.AddIndex(
            model_name="treatmentgoal",
            index=models.Index(fields=["organization", "patient", "status"], name="goal_org_patient_idx"),
        ),
        migrations.AddIndex(
            model_name="clinicaldocument",
            index=models.Index(fields=["organization", "patient", "is_archived"], name="document_org_patient_idx"),
        ),
        migrations.AddIndex(
            model_name="clinicalexport",
            index=models.Index(fields=["organization", "status", "created_at"], name="export_org_status_idx"),
        ),
        migrations.AddIndex(
            model_name="clinicalformresponse",
            index=models.Index(fields=["organization", "patient", "status"], name="form_resp_org_patient_idx"),
        ),
    ]
