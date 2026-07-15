from django.db import migrations


def repair_legacy_in_app_channel(apps, schema_editor):
    channel_config = apps.get_model("communications", "CommunicationChannelConfig")
    channel_config.objects.filter(
        channel="in_app",
        provider="",
        connection_status__in=["not_configured", "incomplete"],
    ).update(
        provider="in_app",
        is_active=True,
        connection_status="configured",
        last_error_code="",
        last_error_message="",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("communications", "0009_channel_configuration"),
    ]

    operations = [
        migrations.RunPython(
            repair_legacy_in_app_channel,
            migrations.RunPython.noop,
        ),
    ]
