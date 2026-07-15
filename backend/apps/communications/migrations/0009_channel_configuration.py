import apps.core.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("communications", "0008_reconcile_runtime_schema"),
    ]

    operations = [
        migrations.AlterField(
            model_name="communicationchannelconfig",
            name="connection_status",
            field=models.CharField(
                choices=[
                    ("not_configured", "Não configurado"),
                    ("incomplete", "Configuração incompleta"),
                    ("validating", "Validando"),
                    ("configured", "Configurado"),
                    ("error", "Com erro"),
                    ("disabled", "Desativado"),
                    ("unavailable", "Indisponível temporariamente"),
                ],
                default="not_configured",
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name="communicationchannelconfig",
            name="credentials",
            field=apps.core.fields.EncryptedTextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="communicationchannelconfig",
            name="last_error_code",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="communicationchannelconfig",
            name="last_error_message",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="communicationchannelconfig",
            name="last_tested_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name="communicationchannelconfig",
            index=models.Index(
                fields=["owner", "is_active", "connection_status"],
                name="comm_channel_oper_idx",
            ),
        ),
    ]
