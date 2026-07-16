# Generated manually for a non-managed permission anchor.

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SQLExplorerPermission",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
            options={
                "verbose_name": "Acesso ao SQL Explorer",
                "verbose_name_plural": "Acessos ao SQL Explorer",
                "permissions": (
                    ("use_sql_explorer", "Pode utilizar o SQL Explorer administrativo"),
                ),
                "default_permissions": (),
                "managed": False,
            },
        ),
    ]
