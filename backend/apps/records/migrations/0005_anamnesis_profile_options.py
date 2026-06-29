from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("records", "0004_evolution_status_and_goal_default")]

    operations = [
        migrations.AlterModelOptions(
            name="anamnesisprofile",
            options={
                "verbose_name": "Perfil ampliado de anamnese",
                "verbose_name_plural": "Perfis ampliados de anamnese",
            },
        ),
    ]
