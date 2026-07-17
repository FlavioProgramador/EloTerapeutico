from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

import apps.core.validators


class Migration(migrations.Migration):
    dependencies = [("users", "0004_authsession")]

    operations = [
        migrations.AddField(model_name="user", name="display_name", field=models.CharField(blank=True, max_length=120, verbose_name="Nome de exibição")),
        migrations.AddField(model_name="user", name="profession", field=models.CharField(blank=True, max_length=100, verbose_name="Profissão")),
        migrations.AddField(model_name="user", name="default_modality", field=models.CharField(choices=[("in_person", "Presencial"), ("online", "Online"), ("hybrid", "Híbrido")], default="in_person", max_length=20, verbose_name="Modalidade padrão")),
        migrations.AddField(model_name="user", name="timezone", field=models.CharField(default="America/Sao_Paulo", max_length=64)),
        migrations.AddField(model_name="user", name="language", field=models.CharField(default="pt-BR", max_length=10)),
        migrations.AddField(model_name="user", name="date_format", field=models.CharField(default="DD/MM/YYYY", max_length=20)),
        migrations.AddField(model_name="user", name="time_format", field=models.CharField(default="24h", max_length=10)),
        migrations.CreateModel(
            name="PracticeSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("trade_name", models.CharField(blank=True, max_length=160)),
                ("document", models.CharField(blank=True, max_length=32)),
                ("phone", models.CharField(blank=True, max_length=20, validators=[apps.core.validators.validate_phone])),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("address", models.JSONField(blank=True, default=dict)),
                ("timezone", models.CharField(default="America/Sao_Paulo", max_length=64)),
                ("currency", models.CharField(default="BRL", max_length=3)),
                ("appointment_interval_minutes", models.PositiveSmallIntegerField(default=0)),
                ("minimum_booking_notice_hours", models.PositiveSmallIntegerField(default=0)),
                ("cancellation_notice_hours", models.PositiveSmallIntegerField(default=24)),
                ("allow_overbooking", models.BooleanField(default=False)),
                ("consider_holidays", models.BooleanField(default=False)),
                ("reminders_enabled", models.BooleanField(default=True)),
                ("reminder_minutes", models.PositiveIntegerField(default=1440)),
                ("internal_communications_enabled", models.BooleanField(default=True)),
                ("message_preview_enabled", models.BooleanField(default=True)),
                ("auto_mark_read", models.BooleanField(default=False)),
                ("mentions_enabled", models.BooleanField(default=True)),
                ("notify_mentions", models.BooleanField(default=True)),
                ("quiet_hours_enabled", models.BooleanField(default=False)),
                ("quiet_hours_start", models.TimeField(blank=True, null=True)),
                ("quiet_hours_end", models.TimeField(blank=True, null=True)),
                ("communication_policy", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="practice_settings", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Configurações da prática", "verbose_name_plural": "Configurações das práticas"},
        ),
    ]
