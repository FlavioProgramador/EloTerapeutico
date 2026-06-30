from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("patients", "0005_sync_patient_admin_fields"),
        ("patients", "0006_patient_registration_invite"),
    ]

    operations = []
