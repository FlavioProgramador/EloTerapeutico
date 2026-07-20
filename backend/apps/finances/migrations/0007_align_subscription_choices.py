from django.db import migrations, models


PAYMENT_METHODS = [("uninformed", "Não informado"), ("pix", "PIX"), ("credit_card", "Cartão de Crédito"), ("debit_card", "Cartão de Débito"), ("cash", "Dinheiro"), ("bank_transfer", "Transferência Bancária"), ("boleto", "Boleto"), ("payment_link", "Link de pagamento"), ("other", "Outro")]


class Migration(migrations.Migration):
    dependencies = [("financeiro", "0006_align_transaction_choices")]
    operations = [
        migrations.AlterField(
            model_name="monthlysubscription",
            name="status",
            field=models.CharField(choices=[("active", "Ativa"), ("paused", "Pausada"), ("ended", "Encerrada"), ("cancelled", "Cancelada")], default="active", max_length=15),
        ),
        migrations.AlterField(
            model_name="monthlysubscription",
            name="frequency",
            field=models.CharField(choices=[("weekly", "Semanal"), ("biweekly", "Quinzenal"), ("monthly", "Mensal")], default="weekly", max_length=15),
        ),
        migrations.AlterField(
            model_name="monthlysubscription",
            name="preferred_payment_method",
            field=models.CharField(choices=PAYMENT_METHODS, default="uninformed", max_length=20),
        ),
        migrations.AlterField(
            model_name="monthlysubscription",
            name="weekday",
            field=models.PositiveSmallIntegerField(help_text="0=segunda-feira, 6=domingo"),
        ),
    ]
