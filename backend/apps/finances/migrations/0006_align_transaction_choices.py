from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("financeiro", "0005_financial_dashboard_and_subscriptions")]
    operations = [
        migrations.AlterField(
            model_name="financialtransaction",
            name="category",
            field=models.CharField(
                choices=[("session", "Sessão"), ("subscription", "Mensalidade"), ("material", "Material"), ("rent", "Aluguel"), ("utilities", "Contas de consumo"), ("taxes", "Impostos"), ("software", "Software"), ("marketing", "Marketing"), ("services", "Serviços"), ("refund", "Reembolso"), ("other", "Outro")],
                default="session",
                max_length=20,
                verbose_name="Categoria",
            ),
        ),
        migrations.AlterField(
            model_name="financialtransaction",
            name="payment_method",
            field=models.CharField(
                choices=[("uninformed", "Não informado"), ("pix", "PIX"), ("credit_card", "Cartão de Crédito"), ("debit_card", "Cartão de Débito"), ("cash", "Dinheiro"), ("bank_transfer", "Transferência Bancária"), ("boleto", "Boleto"), ("payment_link", "Link de pagamento"), ("other", "Outro")],
                default="uninformed",
                max_length=20,
                verbose_name="Método de pagamento",
            ),
        ),
        migrations.AlterField(
            model_name="financialtransaction",
            name="source",
            field=models.CharField(
                choices=[("manual", "Manual"), ("appointment", "Sessão"), ("subscription", "Mensalidade"), ("recurrence", "Recorrência")],
                default="manual",
                max_length=20,
                verbose_name="Origem",
            ),
        ),
        migrations.AlterField(
            model_name="financialtransaction",
            name="recurrence_frequency",
            field=models.CharField(
                blank=True,
                choices=[("weekly", "Semanal"), ("biweekly", "Quinzenal"), ("monthly", "Mensal"), ("quarterly", "Trimestral"), ("semiannual", "Semestral"), ("annual", "Anual")],
                max_length=20,
                verbose_name="Frequência da recorrência",
            ),
        ),
    ]
