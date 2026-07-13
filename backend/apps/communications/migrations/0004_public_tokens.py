# Generated for the Elo Terapêutico communications domain.
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models

import core.fields


class Migration(migrations.Migration):
    dependencies = [
        ("communications", "0003_preferences_notifications"),
    ]

    operations = [
        migrations.CreateModel(
            name="PublicCommunicationActionToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("purpose", models.CharField(choices=[("confirm_appointment", "Confirmar consulta"), ("cancel_request", "Solicitar cancelamento"), ("reschedule_request", "Solicitar reagendamento"), ("form_access", "Acessar formulário"), ("document_access", "Acessar documento"), ("acknowledge", "Confirmar recebimento")], max_length=32)),
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("appointment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="communication_tokens", to="agenda.appointment")),
                ("document", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="communication_tokens", to="documents.generateddocument")),
                ("form_submission", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="communication_tokens", to="forms.formsubmission")),
                ("communication", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="public_tokens", to="communications.communication")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="communication_tokens", to=settings.AUTH_USER_MODEL)),
                ("patient", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="communication_tokens", to="patients.patient")),
            ],
        ),
    ]
