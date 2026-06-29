from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("records", "0003_prontuario_estruturado")]

    operations = [
        migrations.AddField(
            model_name="evolutionclinicaldata",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Rascunho"),
                    ("finalized", "Finalizada"),
                    ("archived", "Arquivada"),
                ],
                db_index=True,
                default="draft",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="evolutionclinicaldata",
            name="finalized_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="evolutionclinicaldata",
            name="archived_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="treatmentgoal",
            name="start_date",
            field=models.DateField(default=django.utils.timezone.localdate),
        ),
    ]
