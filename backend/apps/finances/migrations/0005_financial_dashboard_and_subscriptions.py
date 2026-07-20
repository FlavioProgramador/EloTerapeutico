from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("financeiro", "0004_alter_financialtransaction_payment_status")]

    operations = [
        migrations.AlterField(
            model_name="financialtransaction",
            name="amount",
            field=models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Valor"),
        ),
        migrations.AlterField(
            model_name="financialtransaction",
            name="payment_status",
            field=models.CharField(
                choices=[
                    ("paid", "Pago"),
                    ("partial", "Parcialmente pago"),
                    ("pending", "Pendente"),
                    ("cancelled", "Cancelado"),
                    ("refunded", "Estornado"),
                ],
                default="pending",
                max_length=15,
                verbose_name="Status",
            ),
        ),
        migrations.AddField(
            model_name="financialtransaction",
            name="paid_amount",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12, verbose_name="Valor pago"),
        ),
        migrations.AddField(
            model_name="financialtransaction",
            name="beneficiary",
            field=models.CharField(blank=True, max_length=180, verbose_name="Beneficiário"),
        ),
        migrations.AddField(
            model_name="financialtransaction",
            name="payment_link",
            field=models.URLField(blank=True, verbose_name="Link de pagamento"),
        ),
        migrations.AddField(
            model_name="financialtransaction",
            name="source",
            field=models.CharField(default="manual", max_length=20, verbose_name="Origem"),
        ),
        migrations.AddField(
            model_name="financialtransaction",
            name="is_recurring",
            field=models.BooleanField(default=False, verbose_name="Recorrente"),
        ),
        migrations.AddField(
            model_name="financialtransaction",
            name="recurrence_frequency",
            field=models.CharField(blank=True, max_length=20, verbose_name="Frequência da recorrência"),
        ),
        migrations.AddField(
            model_name="financialtransaction",
            name="recurrence_end_date",
            field=models.DateField(blank=True, null=True, verbose_name="Fim da recorrência"),
        ),
        migrations.CreateModel(
            name="MonthlySubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(default="active", max_length=15)),
                ("frequency", models.CharField(default="weekly", max_length=15)),
                ("weekday", models.PositiveSmallIntegerField()),
                ("appointment_time", models.TimeField()),
                ("first_appointment_date", models.DateField()),
                ("duration_minutes", models.PositiveSmallIntegerField(default=50)),
                ("timezone", models.CharField(default="America/Sao_Paulo", max_length=64)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("occurrence_limit", models.PositiveIntegerField(blank=True, null=True)),
                ("monthly_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("due_day", models.PositiveSmallIntegerField(default=5)),
                ("first_due_date", models.DateField(blank=True, null=True)),
                ("next_billing_date", models.DateField(blank=True, null=True)),
                ("reminder_days_before", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("preferred_payment_method", models.CharField(default="uninformed", max_length=20)),
                ("payment_link", models.URLField(blank=True)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="monthly_subscriptions", to="patients.patient")),
                ("therapist", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="monthly_subscriptions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["patient__full_name"]},
        ),
        migrations.AddField(
            model_name="financialtransaction",
            name="subscription",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="charges", to="financeiro.monthlysubscription", verbose_name="Mensalidade"),
        ),
    ]
