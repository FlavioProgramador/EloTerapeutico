# Generated manually for billing app.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Plan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, verbose_name="Nome")),
                ("slug", models.SlugField(unique=True, verbose_name="Slug")),
                ("description", models.TextField(blank=True, verbose_name="Descrição")),
                ("price", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Preço")),
                ("currency", models.CharField(default="BRL", max_length=3, verbose_name="Moeda")),
                ("billing_cycle", models.CharField(choices=[("MONTHLY", "Mensal"), ("YEARLY", "Anual")], default="MONTHLY", max_length=20, verbose_name="Ciclo de cobrança")),
                ("is_active", models.BooleanField(default=True, verbose_name="Ativo")),
                ("max_patients", models.PositiveIntegerField(blank=True, null=True, verbose_name="Limite de pacientes")),
                ("max_storage_mb", models.PositiveIntegerField(blank=True, null=True, verbose_name="Limite de armazenamento (MB)")),
                ("has_agenda", models.BooleanField(default=True, verbose_name="Agenda")),
                ("has_patients", models.BooleanField(default=True, verbose_name="Pacientes")),
                ("has_clinical_records", models.BooleanField(default=True, verbose_name="Prontuários")),
                ("has_financial", models.BooleanField(default=False, verbose_name="Financeiro")),
                ("has_documents", models.BooleanField(default=False, verbose_name="Documentos")),
                ("has_forms", models.BooleanField(default=False, verbose_name="Formulários")),
                ("has_reports", models.BooleanField(default=False, verbose_name="Relatórios")),
                ("has_ai", models.BooleanField(default=False, verbose_name="IA")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
            ],
            options={"verbose_name": "Plano", "verbose_name_plural": "Planos", "ordering": ["price", "name"]},
        ),
        migrations.CreateModel(
            name="Subscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("TRIALING", "Em teste"), ("PENDING", "Pendente"), ("ACTIVE", "Ativa"), ("PAST_DUE", "Em atraso"), ("CANCELED", "Cancelada"), ("EXPIRED", "Expirada")], db_index=True, default="PENDING", max_length=20)),
                ("started_at", models.DateTimeField(blank=True, null=True, verbose_name="Iniciada em")),
                ("trial_ends_at", models.DateTimeField(blank=True, null=True, verbose_name="Fim do trial")),
                ("current_period_start", models.DateTimeField(blank=True, null=True, verbose_name="Início do período atual")),
                ("current_period_end", models.DateTimeField(blank=True, null=True, verbose_name="Fim do período atual")),
                ("canceled_at", models.DateTimeField(blank=True, null=True, verbose_name="Cancelada em")),
                ("gateway_name", models.CharField(default="ASAAS", max_length=40)),
                ("gateway_customer_id", models.CharField(blank=True, max_length=120)),
                ("gateway_subscription_id", models.CharField(blank=True, db_index=True, max_length=120)),
                ("gateway_status", models.CharField(blank=True, max_length=80)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criada em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizada em")),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="subscriptions", to="billing.plan", verbose_name="Plano")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="subscriptions", to=settings.AUTH_USER_MODEL, verbose_name="Usuário")),
            ],
            options={"verbose_name": "Assinatura", "verbose_name_plural": "Assinaturas", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="WebhookEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("gateway_name", models.CharField(max_length=40)),
                ("event_id", models.CharField(blank=True, max_length=160, null=True, unique=True)),
                ("event_type", models.CharField(max_length=120)),
                ("payload_hash", models.CharField(max_length=64, unique=True)),
                ("payload", models.JSONField()),
                ("processed", models.BooleanField(default=False)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True)),
                ("received_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "Evento de webhook", "verbose_name_plural": "Eventos de webhook", "ordering": ["-received_at"]},
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("currency", models.CharField(default="BRL", max_length=3)),
                ("status", models.CharField(choices=[("PENDING", "Pendente"), ("CONFIRMED", "Confirmado"), ("RECEIVED", "Recebido"), ("OVERDUE", "Vencido"), ("REFUNDED", "Estornado"), ("CANCELED", "Cancelado"), ("FAILED", "Falhou")], db_index=True, default="PENDING", max_length=20)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("gateway_name", models.CharField(default="ASAAS", max_length=40)),
                ("gateway_payment_id", models.CharField(blank=True, max_length=120, null=True, unique=True)),
                ("gateway_subscription_id", models.CharField(blank=True, db_index=True, max_length=120)),
                ("invoice_url", models.URLField(blank=True)),
                ("bank_slip_url", models.URLField(blank=True)),
                ("pix_qr_code", models.TextField(blank=True)),
                ("pix_copy_paste", models.TextField(blank=True)),
                ("raw_payload", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("subscription", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to="billing.subscription")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="billing_payments", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Pagamento", "verbose_name_plural": "Pagamentos", "ordering": ["-due_date", "-created_at"]},
        ),
        migrations.CreateModel(
            name="FeatureUsage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("feature_key", models.CharField(max_length=80)),
                ("usage_count", models.PositiveIntegerField(default=0)),
                ("period_start", models.DateTimeField()),
                ("period_end", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="feature_usages", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Uso de recurso", "verbose_name_plural": "Uso de recursos", "ordering": ["-period_start"], "unique_together": {("user", "feature_key", "period_start", "period_end")}},
        ),
        migrations.AddIndex(model_name="subscription", index=models.Index(fields=["user", "status"], name="billing_sub_user_status_idx")),
        migrations.AddIndex(model_name="subscription", index=models.Index(fields=["gateway_subscription_id"], name="billing_sub_gateway_idx")),
        migrations.AddIndex(model_name="webhookevent", index=models.Index(fields=["gateway_name", "event_type"], name="billing_webhook_type_idx")),
        migrations.AddIndex(model_name="payment", index=models.Index(fields=["user", "status"], name="billing_pay_user_status_idx")),
        migrations.AddIndex(model_name="payment", index=models.Index(fields=["gateway_subscription_id"], name="billing_pay_sub_gateway_idx")),
    ]
