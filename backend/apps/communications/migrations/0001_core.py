# Generated for the Elo Terapêutico communications domain.
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models

import apps.core.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("patients", "0009_normalize_patient_tags"),
        ("agenda", "0004_agenda_complete_domain"),
        ("forms", "0001_initial"),
        ("documents", "0002_seed_library"),
        ("financeiro", "0011_unique_appointment_source"),
    ]

    operations = [
        migrations.CreateModel(
            name="CommunicationTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("slug", models.SlugField(max_length=180)),
                ("description", models.TextField(blank=True)),
                ("category", models.CharField(choices=[("appointment_confirmation", "Confirmação de consulta"), ("appointment_reminder", "Lembrete de consulta"), ("appointment_rescheduled", "Consulta reagendada"), ("appointment_canceled", "Consulta cancelada"), ("form_request", "Solicitação de formulário"), ("form_reminder", "Lembrete de formulário"), ("document_available", "Documento disponível"), ("document_signature", "Assinatura de documento"), ("payment_due", "Pagamento próximo do vencimento"), ("payment_overdue", "Pagamento vencido"), ("payment_confirmed", "Pagamento confirmado"), ("package_ending", "Pacote próximo do fim"), ("patient_message", "Mensagem ao paciente"), ("system_notification", "Notificação do sistema"), ("other", "Outro")], max_length=40)),
                ("channel", models.CharField(choices=[("in_app", "Notificação interna"), ("email", "E-mail"), ("whatsapp_manual", "WhatsApp manual"), ("whatsapp", "WhatsApp Business"), ("sms", "SMS")], max_length=24)),
                ("subject_template", models.CharField(blank=True, max_length=255)),
                ("body_template", models.TextField()),
                ("allowed_variables", models.JSONField(blank=True, default=list)),
                ("is_system_template", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("is_archived", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_communication_templates", to=settings.AUTH_USER_MODEL)),
                ("owner", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="communication_templates", to=settings.AUTH_USER_MODEL)),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="updated_communication_templates", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="CommunicationAutomation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=160)),
                ("description", models.TextField(blank=True)),
                ("event_type", models.CharField(db_index=True, max_length=80)),
                ("channel", models.CharField(choices=[("in_app", "Notificação interna"), ("email", "E-mail"), ("whatsapp_manual", "WhatsApp manual"), ("whatsapp", "WhatsApp Business"), ("sms", "SMS")], max_length=24)),
                ("is_active", models.BooleanField(db_index=True, default=False)),
                ("delay_value", models.PositiveIntegerField(default=0)),
                ("delay_unit", models.CharField(choices=[("minutes", "Minutos"), ("hours", "Horas"), ("days", "Dias")], default="minutes", max_length=12)),
                ("send_before_event", models.BooleanField(default=False)),
                ("conditions", models.JSONField(blank=True, default=list)),
                ("allowed_start_time", models.TimeField(blank=True, null=True)),
                ("allowed_end_time", models.TimeField(blank=True, null=True)),
                ("allowed_weekdays", models.JSONField(blank=True, default=list)),
                ("respect_preferences", models.BooleanField(default=True)),
                ("max_executions", models.PositiveIntegerField(blank=True, null=True)),
                ("priority", models.CharField(choices=[("low", "Baixa"), ("normal", "Normal"), ("high", "Alta")], default="normal", max_length=12)),
                ("fallback_channel", models.CharField(blank=True, choices=[("in_app", "Notificação interna"), ("email", "E-mail"), ("whatsapp_manual", "WhatsApp manual"), ("whatsapp", "WhatsApp Business"), ("sms", "SMS")], max_length=24)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_communication_automations", to=settings.AUTH_USER_MODEL)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="communication_automations", to=settings.AUTH_USER_MODEL)),
                ("template", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="automations", to="communications.communicationtemplate")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="updated_communication_automations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Communication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("direction", models.CharField(choices=[("outbound", "Saída"), ("inbound", "Entrada")], default="outbound", max_length=12)),
                ("channel", models.CharField(choices=[("in_app", "Notificação interna"), ("email", "E-mail"), ("whatsapp_manual", "WhatsApp manual"), ("whatsapp", "WhatsApp Business"), ("sms", "SMS")], db_index=True, max_length=24)),
                ("category", models.CharField(choices=[("appointment_confirmation", "Confirmação de consulta"), ("appointment_reminder", "Lembrete de consulta"), ("appointment_rescheduled", "Consulta reagendada"), ("appointment_canceled", "Consulta cancelada"), ("form_request", "Solicitação de formulário"), ("form_reminder", "Lembrete de formulário"), ("document_available", "Documento disponível"), ("document_signature", "Assinatura de documento"), ("payment_due", "Pagamento próximo do vencimento"), ("payment_overdue", "Pagamento vencido"), ("payment_confirmed", "Pagamento confirmado"), ("package_ending", "Pacote próximo do fim"), ("patient_message", "Mensagem ao paciente"), ("system_notification", "Notificação do sistema"), ("other", "Outro")], db_index=True, default="other", max_length=40)),
                ("status", models.CharField(choices=[("draft", "Rascunho"), ("scheduled", "Agendada"), ("queued", "Na fila"), ("processing", "Processando"), ("sent", "Enviada"), ("delivered", "Entregue"), ("read", "Lida"), ("responded", "Respondida"), ("failed", "Falhou"), ("canceled", "Cancelada"), ("expired", "Expirada")], db_index=True, default="draft", max_length=20)),
                ("priority", models.CharField(choices=[("low", "Baixa"), ("normal", "Normal"), ("high", "Alta")], default="normal", max_length=12)),
                ("subject", models.CharField(blank=True, max_length=255)),
                ("body", apps.core.fields.EncryptedTextField(blank=True)),
                ("body_html", apps.core.fields.EncryptedTextField(blank=True)),
                ("structured_content", models.JSONField(blank=True, default=dict)),
                ("template_snapshot", models.JSONField(blank=True, default=dict)),
                ("variables_snapshot", models.JSONField(blank=True, default=dict)),
                ("scheduled_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("queued_at", models.DateTimeField(blank=True, null=True)),
                ("next_retry_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("processing_started_at", models.DateTimeField(blank=True, null=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("responded_at", models.DateTimeField(blank=True, null=True)),
                ("failed_at", models.DateTimeField(blank=True, null=True)),
                ("canceled_at", models.DateTimeField(blank=True, null=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("idempotency_key", models.CharField(max_length=160)),
                ("source_event", models.CharField(blank=True, db_index=True, max_length=80)),
                ("source_object_type", models.CharField(blank=True, max_length=80)),
                ("source_object_id", models.CharField(blank=True, max_length=80)),
                ("provider_name", models.CharField(blank=True, max_length=60)),
                ("provider_message_id", models.CharField(blank=True, db_index=True, max_length=160)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("archived_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("appointment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="communications", to="agenda.appointment")),
                ("document", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="communications", to="documents.generateddocument")),
                ("financial_transaction", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="communications", to="financeiro.financialtransaction")),
                ("form_submission", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="communications", to="forms.formsubmission")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_communications", to=settings.AUTH_USER_MODEL)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="communications", to=settings.AUTH_USER_MODEL, verbose_name="Proprietário")),
                ("patient", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="communications", to="patients.patient")),
                ("template", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="communications", to="communications.communicationtemplate")),
            ],
            options={"verbose_name": "Comunicação", "verbose_name_plural": "Comunicações", "ordering": ["-created_at"]},
        ),
    ]
