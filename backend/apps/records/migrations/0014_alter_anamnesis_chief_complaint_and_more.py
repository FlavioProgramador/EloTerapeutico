import apps.core.fields
import apps.records.treatment_models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("records", "0013_record_organizations"),
    ]

    operations = [
        migrations.AlterField(
            model_name="anamnesis",
            name="chief_complaint",
            field=apps.core.fields.EncryptedTextField(verbose_name="Queixa principal"),
        ),
        migrations.AlterField(
            model_name="anamnesis",
            name="family_history",
            field=apps.core.fields.EncryptedTextField(
                blank=True,
                verbose_name="Histórico familiar",
            ),
        ),
        migrations.AlterField(
            model_name="anamnesis",
            name="history",
            field=apps.core.fields.EncryptedTextField(
                blank=True,
                verbose_name="Histórico clínico",
            ),
        ),
        migrations.AlterField(
            model_name="anamnesis",
            name="medications",
            field=apps.core.fields.EncryptedTextField(
                blank=True,
                verbose_name="Medicações em uso",
            ),
        ),
        migrations.AlterField(
            model_name="anamnesis",
            name="observations",
            field=apps.core.fields.EncryptedTextField(
                blank=True,
                verbose_name="Observações gerais",
            ),
        ),
        migrations.AlterField(
            model_name="anamnesis",
            name="organization",
            field=models.ForeignKey(
                db_index=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="records_anamnesis_items",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="anamnesis",
            name="patient",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="anamnesis",
                to="patients.patient",
                verbose_name="Paciente",
            ),
        ),
        migrations.AlterField(
            model_name="clinicaldocument",
            name="file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=apps.records.treatment_models.clinical_document_path,
            ),
        ),
        migrations.AlterField(
            model_name="clinicaldocument",
            name="organization",
            field=models.ForeignKey(
                db_index=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="records_clinicaldocument_items",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="clinicaldocument",
            name="quarantine_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to=apps.records.treatment_models.clinical_document_quarantine_path,
            ),
        ),
        migrations.AlterField(
            model_name="clinicalexport",
            name="organization",
            field=models.ForeignKey(
                db_index=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="records_clinicalexport_items",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="clinicalformresponse",
            name="organization",
            field=models.ForeignKey(
                db_index=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="records_clinicalformresponse_items",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="evolution",
            name="appointment",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="evolution",
                to="agenda.appointment",
                verbose_name="Agendamento vinculado",
            ),
        ),
        migrations.AlterField(
            model_name="evolution",
            name="cid10",
            field=models.CharField(
                blank=True,
                max_length=10,
                verbose_name="CID-10",
            ),
        ),
        migrations.AlterField(
            model_name="evolution",
            name="content",
            field=apps.core.fields.EncryptedTextField(
                verbose_name="Conteúdo da sessão",
            ),
        ),
        migrations.AlterField(
            model_name="evolution",
            name="is_confidential",
            field=models.BooleanField(
                default=False,
                verbose_name="Confidencial",
            ),
        ),
        migrations.AlterField(
            model_name="evolution",
            name="is_locked",
            field=models.BooleanField(
                default=False,
                verbose_name="Bloqueada",
            ),
        ),
        migrations.AlterField(
            model_name="evolution",
            name="locked_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Bloqueada em",
            ),
        ),
        migrations.AlterField(
            model_name="evolution",
            name="organization",
            field=models.ForeignKey(
                db_index=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="records_evolution_items",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="evolution",
            name="session_date",
            field=models.DateField(verbose_name="Data da sessão"),
        ),
        migrations.AlterField(
            model_name="treatmentgoal",
            name="organization",
            field=models.ForeignKey(
                db_index=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="records_treatmentgoal_items",
                to="organizations.organization",
            ),
        ),
    ]
