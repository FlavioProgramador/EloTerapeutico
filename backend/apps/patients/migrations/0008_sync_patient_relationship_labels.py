import core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("patients", "0007_merge_patient_migrations"),
    ]

    operations = [
        migrations.AlterField(
            model_name="patient",
            name="emergency_contact_relationship",
            field=models.CharField(
                blank=True,
                max_length=80,
                verbose_name="Relação do contato",
            ),
        ),
        migrations.AlterField(
            model_name="patient",
            name="guardian_name",
            field=models.CharField(
                blank=True,
                max_length=255,
                verbose_name="Nome do responsável legal",
            ),
        ),
        migrations.AlterField(
            model_name="patient",
            name="guardian_cpf",
            field=models.CharField(
                blank=True,
                max_length=11,
                validators=[core.validators.validate_cpf],
                verbose_name="CPF do responsável legal",
            ),
        ),
        migrations.AlterField(
            model_name="patient",
            name="guardian_phone",
            field=models.CharField(
                blank=True,
                max_length=20,
                validators=[core.validators.validate_phone],
                verbose_name="Telefone do responsável legal",
            ),
        ),
        migrations.AlterField(
            model_name="patient",
            name="guardian_email",
            field=models.EmailField(
                blank=True,
                max_length=254,
                verbose_name="E-mail do responsável legal",
            ),
        ),
        migrations.AlterField(
            model_name="patient",
            name="guardian_relationship",
            field=models.CharField(
                blank=True,
                max_length=80,
                verbose_name="Relação do responsável legal",
            ),
        ),
    ]
