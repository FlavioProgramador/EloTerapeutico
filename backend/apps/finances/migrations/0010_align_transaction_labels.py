from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("financeiro", "0009_financial_constraints")]
    operations = [
        migrations.AlterField(
            model_name="financialtransaction",
            name="description",
            field=models.TextField(blank=True, verbose_name="Descrição"),
        ),
        migrations.AlterField(
            model_name="financialtransaction",
            name="due_date",
            field=models.DateField(blank=True, null=True, verbose_name="Vencimento"),
        ),
        migrations.AlterField(
            model_name="financialtransaction",
            name="receipt_url",
            field=models.URLField(blank=True, verbose_name="URL do recibo"),
        ),
    ]
