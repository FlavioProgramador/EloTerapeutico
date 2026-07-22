import apps.scheduling.models.remote
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("agenda", "0006_telemedicine_media_domain")]

    operations = [
        migrations.AlterField(
            model_name="telemedicineroom",
            name="provider_room_name",
            field=models.CharField(
                default=apps.scheduling.models.remote.generate_provider_room_name,
                editable=False,
                max_length=80,
                unique=True,
            ),
        ),
    ]
