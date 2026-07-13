# Generated for the Elo Terapêutico communications domain.
import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models

import apps.core.fields
from apps.communications.migration_operations import CreateModelIfNotExists


class Migration(migrations.Migration):
    dependencies = [
        ("communications", "0001_core"),
    ]

    operations = [
        CreateModelIfNotExists(
            name="CommunicationRecipient",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("recipient_type", models.CharField(choices=[("patient", "Paciente"), ("guardian", "Responsável legal"), ("professional", "Profissional"), ("user", "Usuário"), ("custom", "Personalizado")], max_length=20)),
                ("name", models.CharField(max_length=255)),
                ("destination", apps.core.fields.EncryptedTextField()),
                ("destination_masked", models.CharField(max_length=255)),
                ("channel", models.CharField(choices=[("in_app", "Notificação interna"), ("email", "E-mail"), ("whatsapp_manual", "WhatsApp manual"), ("whatsapp", "WhatsApp Business"), ("sms", "SMS")], max_length=24)),
                ("status", models.CharField(choices=[("pending", "Pendente"), ("ready", "Pronto"), ("blocked", "Bloqueado"), ("sent", "Enviado"), ("failed", "Falhou")], default="pending", max_length=20)),
                ("blocked_reason", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("communication", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recipients", to="communications.communication")),
                ("patient", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="communication_recipients", to="patients.patient")),
            ],
            options={"ordering": ["id"]},
        ),
        CreateModelIfNotExists(
            name="CommunicationAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("attempt_number", models.PositiveSmallIntegerField()),
                ("provider", models.CharField(max_length=60)),
                ("status", models.CharField(choices=[("pending", "Pendente"), ("processing", "Processando"), ("success", "Sucesso"), ("retryable_failure", "Falha temporária"), ("permanent_failure", "Falha permanente")], default="pending", max_length=32)),
                ("external_id", models.CharField(blank=True, max_length=160)),
                ("response_code", models.CharField(blank=True, max_length=40)),
                ("error_code", models.CharField(blank=True, max_length=80)),
                ("error_message", models.CharField(blank=True, max_length=500)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("next_retry_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("latency_ms", models.PositiveIntegerField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("communication", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to="communications.communication")),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to="communications.communicationrecipient")),
            ],
            options={"ordering": ["communication", "recipient", "attempt_number"]},
        ),
        CreateModelIfNotExists(
            name="CommunicationAutomationRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_event", models.CharField(max_length=80)),
                ("source_object_type", models.CharField(blank=True, max_length=80)),
                ("source_object_id", models.CharField(blank=True, max_length=80)),
                ("status", models.CharField(choices=[("started", "Iniciada"), ("created", "Comunicação criada"), ("skipped", "Ignorada"), ("failed", "Falhou")], default="started", max_length=20)),
                ("skip_reason", models.CharField(blank=True, max_length=255)),
                ("idempotency_key", models.CharField(max_length=160)),
                ("error_message", models.CharField(blank=True, max_length=500)),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("automation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="runs", to="communications.communicationautomation")),
                ("communication", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="automation_runs", to="communications.communication")),
            ],
            options={"ordering": ["-started_at"]},
        ),
    ]
