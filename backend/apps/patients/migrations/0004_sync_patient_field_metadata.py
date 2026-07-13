import apps.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("patients", "0003_patient_workspace")]
    operations = [
        migrations.AlterField(
            model_name="patient",
            name="cpf",
            field=models.CharField(
                max_length=11,
                unique=True,
                validators=[apps.core.validators.validate_cpf],
                verbose_name="CPF",
            ),
        ),
        migrations.AlterField(
            model_name="patient",
            name="phone",
            field=models.CharField(
                blank=True,
                max_length=20,
                validators=[apps.core.validators.validate_phone],
                verbose_name="Telefone",
            ),
        ),
        migrations.AlterField(
            model_name="patient",
            name="address",
            field=models.JSONField(blank=True, default=dict, verbose_name="Endereço"),
        ),
        migrations.AlterField(
            model_name="patient",
            name="referral_source",
            field=models.CharField(blank=True, max_length=255, verbose_name="Origem / indicação"),
        ),
    ]
