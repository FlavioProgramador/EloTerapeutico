from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("financeiro", "0008_financial_indexes")]
    operations = [
        migrations.AddConstraint(
            model_name="financialtransaction",
            constraint=models.CheckConstraint(condition=models.Q(amount__gt=0), name="fin_amount_positive"),
        ),
        migrations.AddConstraint(
            model_name="financialtransaction",
            constraint=models.CheckConstraint(condition=models.Q(paid_amount__gte=0), name="fin_paid_amount_non_negative"),
        ),
        migrations.AddConstraint(
            model_name="financialtransaction",
            constraint=models.CheckConstraint(condition=models.Q(paid_amount__lte=models.F("amount")), name="fin_paid_amount_lte_amount"),
        ),
        migrations.AddConstraint(
            model_name="monthlysubscription",
            constraint=models.CheckConstraint(condition=models.Q(monthly_amount__gt=0), name="fin_sub_amount_positive"),
        ),
        migrations.AddConstraint(
            model_name="monthlysubscription",
            constraint=models.CheckConstraint(condition=models.Q(due_day__gte=1, due_day__lte=28), name="fin_sub_due_day_valid"),
        ),
        migrations.AddConstraint(
            model_name="monthlysubscription",
            constraint=models.CheckConstraint(condition=models.Q(weekday__gte=0, weekday__lte=6), name="fin_sub_weekday_valid"),
        ),
        migrations.AddConstraint(
            model_name="monthlysubscription",
            constraint=models.CheckConstraint(condition=models.Q(duration_minutes__gte=15), name="fin_sub_duration_min"),
        ),
    ]
