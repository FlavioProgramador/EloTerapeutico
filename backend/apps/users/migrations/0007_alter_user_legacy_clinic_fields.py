from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0006_backfill_default_clinics"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("therapist", "Terapeuta"),
                    ("secretary", "Secretária"),
                    ("admin", "Administrador"),
                ],
                default="therapist",
                help_text="Não utilizar como substituto do papel no membership da clínica.",
                max_length=20,
                verbose_name="Papel global legado",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="clinic_name",
            field=models.CharField(
                blank=True,
                help_text="Mantido temporariamente durante a migração para Clinic.",
                max_length=160,
                verbose_name="Nome da clínica legado",
            ),
        ),
    ]
