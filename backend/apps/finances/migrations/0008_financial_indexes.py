from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("financeiro", "0007_align_subscription_choices")]
    operations = [
        migrations.AddIndex(
            model_name="financialtransaction",
            index=models.Index(fields=["therapist", "due_date"], name="fin_therapist_due_idx"),
        ),
        migrations.AddIndex(
            model_name="financialtransaction",
            index=models.Index(fields=["therapist", "transaction_type", "due_date"], name="fin_type_due_idx"),
        ),
        migrations.AddIndex(
            model_name="monthlysubscription",
            index=models.Index(fields=["therapist", "status"], name="fin_sub_status_idx"),
        ),
        migrations.AddIndex(
            model_name="monthlysubscription",
            index=models.Index(fields=["therapist", "next_billing_date"], name="fin_sub_next_bill_idx"),
        ),
    ]
