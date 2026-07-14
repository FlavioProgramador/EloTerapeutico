import apps.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("patients", "0004_sync_patient_field_metadata"),
        ("patients", "0003_alter_patient_status"),
    ]
    operations = [
        migrations.AlterField(
            model_name="patient",
            name="status",
            field=models.CharField(
                choices=[
                    ("active", "Ativo"),
                    ("evaluation", "Em avaliação"),
                    ("waiting_return", "Aguardando retorno"),
                    ("discharged", "Alta"),
                    ("inactive", "Encerrado"),
                    ("archived", "Arquivado"),
                ],
                db_index=True,
                default="active",
                max_length=20,
                verbose_name="Status",
            ),
        ),
        migrations.AlterField(
            model_name="patient",
            name="guardian_name",
            field=models.CharField(blank=True, max_length=255, verbose_name="Nome do responsável"),
        ),
        migrations.AlterField(
            model_name="patient",
            name="guardian_cpf",
            field=models.CharField(
                blank=True,
                max_length=11,
                validators=[apps.core.validators.validate_cpf],
                verbose_name="CPF do responsável",
            ),
        ),
        migrations.AlterField(
            model_name="patient",
            name="notes",
            field=models.TextField(blank=True, verbose_name="Observações administrativas"),
        ),
        migrations.AlterField(
            model_name="patient",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Ativo"),
        ),
        migrations.AlterField(
            model_name="patient",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Arquivado em"),
        ),
    ]
