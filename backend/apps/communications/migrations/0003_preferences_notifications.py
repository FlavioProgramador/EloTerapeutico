# Generated for the Elo Terapêutico communications domain.
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models

import core.fields


class Migration(migrations.Migration):
    dependencies = [
        ("communications", "0002_delivery"),
    ]

    operations = [
        migrations.CreateModel(
            name="CommunicationPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("preferred_channel", models.CharField(choices=[("email", "E-mail"), ("whatsapp_manual", "WhatsApp"), ("in_app", "Notificação interna")], default="email", max_length=24)),
                ("allow_email", models.BooleanField(default=True)),
                ("allow_whatsapp", models.BooleanField(default=False)),
                ("allow_sms", models.BooleanField(default=False)),
                ("allow_reminders", models.BooleanField(default=True)),
                ("allow_financial_notices", models.BooleanField(default=True)),
                ("allow_form_requests", models.BooleanField(default=True)),
                ("allowed_start_time", models.TimeField(blank=True, null=True)),
                ("allowed_end_time", models.TimeField(blank=True, null=True)),
                ("timezone", models.CharField(default="America/Sao_Paulo", max_length=64)),
                ("general_opt_out", models.BooleanField(default=False)),
                ("opt_out_reason", models.CharField(blank=True, max_length=255)),
                ("opted_out_at", models.DateTimeField(blank=True, null=True)),
                ("consent_source", models.CharField(blank=True, max_length=80)),
                ("consented_at", models.DateTimeField(blank=True, null=True)),
                ("send_to_guardian", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("consent_recorded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="recorded_communication_consents", to=settings.AUTH_USER_MODEL)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="communication_preferences", to=settings.AUTH_USER_MODEL)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="communication_preferences", to="patients.patient")),
            ],
            options={"ordering": ["patient_id"]},
        ),
        migrations.CreateModel(
            name="InAppNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160)),
                ("message", models.CharField(max_length=500)),
                ("notification_type", models.CharField(db_index=True, max_length=80)),
                ("priority", models.CharField(choices=[("low", "Baixa"), ("normal", "Normal"), ("high", "Alta")], default="normal", max_length=12)),
                ("internal_url", models.CharField(blank=True, max_length=500)),
                ("is_read", models.BooleanField(db_index=True, default=False)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("communication", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="notifications", to="communications.communication")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="owned_notifications", to=settings.AUTH_USER_MODEL)),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="in_app_notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="InboundMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("sender_masked", models.CharField(max_length=255)),
                ("channel", models.CharField(choices=[("in_app", "Notificação interna"), ("email", "E-mail"), ("whatsapp_manual", "WhatsApp manual"), ("whatsapp", "WhatsApp Business"), ("sms", "SMS")], max_length=24)),
                ("provider", models.CharField(max_length=60)),
                ("external_id", models.CharField(max_length=160)),
                ("body", core.fields.EncryptedTextField(blank=True)),
                ("status", models.CharField(choices=[("unmatched", "Não identificada"), ("received", "Recebida"), ("reviewed", "Revisada"), ("linked", "Relacionada"), ("archived", "Arquivada")], default="received", max_length=20)),
                ("received_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("communication", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="inbound_messages", to="communications.communication")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="inbound_messages", to=settings.AUTH_USER_MODEL)),
                ("patient", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="inbound_messages", to="patients.patient")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_inbound_messages", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="CommunicationChannelConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("channel", models.CharField(choices=[("in_app", "Notificação interna"), ("email", "E-mail"), ("whatsapp_manual", "WhatsApp manual"), ("whatsapp", "WhatsApp Business"), ("sms", "SMS")], max_length=24)),
                ("provider", models.CharField(blank=True, max_length=60)),
                ("is_active", models.BooleanField(default=False)),
                ("sender", models.CharField(blank=True, max_length=160)),
                ("public_identifier", models.CharField(blank=True, max_length=160)),
                ("connection_status", models.CharField(choices=[("not_configured", "Não configurado"), ("configured", "Configurado"), ("error", "Com erro"), ("disabled", "Desativado")], default="not_configured", max_length=24)),
                ("last_validated_at", models.DateTimeField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="communication_channel_configs", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
