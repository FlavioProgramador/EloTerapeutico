# Generated for the Elo Terapêutico communications domain.
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models

import core.fields


class Migration(migrations.Migration):
    dependencies = [
        ("communications", "0004_public_tokens"),
    ]

    operations = [
        migrations.AddConstraint(model_name="communicationtemplate", constraint=models.UniqueConstraint(fields=("owner", "slug", "channel"), name="comm_template_owner_slug_uniq")),
        migrations.AddConstraint(model_name="communicationtemplate", constraint=models.UniqueConstraint(condition=models.Q(("owner__isnull", True)), fields=("slug", "channel"), name="comm_system_template_slug_uniq")),
        migrations.AddConstraint(model_name="communicationtemplate", constraint=models.CheckConstraint(condition=models.Q(("is_system_template", False), ("owner__isnull", True), _connector="OR"), name="comm_system_template_without_owner")),
        migrations.AddIndex(model_name="communicationtemplate", index=models.Index(fields=["owner", "is_active", "is_archived"], name="comm_template_owner_idx")),
        migrations.AddIndex(model_name="communicationautomation", index=models.Index(fields=["owner", "is_active", "event_type"], name="comm_auto_event_idx")),
        migrations.AddConstraint(model_name="communication", constraint=models.UniqueConstraint(fields=("owner", "idempotency_key"), name="comm_owner_idempotency_uniq")),
        migrations.AddConstraint(model_name="communication", constraint=models.CheckConstraint(condition=models.Q(("scheduled_at__isnull", True), ("status__in", ["scheduled", "queued", "processing", "sent", "delivered", "read", "responded", "failed", "canceled", "expired"]), _connector="OR"), name="comm_schedule_status_valid")),
        migrations.AddIndex(model_name="communication", index=models.Index(fields=["owner", "status"], name="comm_owner_status_idx")),
        migrations.AddIndex(model_name="communication", index=models.Index(fields=["owner", "channel"], name="comm_owner_channel_idx")),
        migrations.AddIndex(model_name="communication", index=models.Index(fields=["owner", "patient"], name="comm_owner_patient_idx")),
        migrations.AddIndex(model_name="communication", index=models.Index(fields=["scheduled_at", "status"], name="comm_due_queue_idx")),
        migrations.AddIndex(model_name="communicationrecipient", index=models.Index(fields=["communication", "status"], name="comm_recipient_status_idx")),
        migrations.AddConstraint(model_name="communicationattempt", constraint=models.UniqueConstraint(fields=("communication", "recipient", "attempt_number"), name="comm_attempt_number_uniq")),
        migrations.AddIndex(model_name="communicationattempt", index=models.Index(fields=["status", "next_retry_at"], name="comm_attempt_retry_idx")),
        migrations.AddConstraint(model_name="communicationautomationrun", constraint=models.UniqueConstraint(fields=("automation", "idempotency_key"), name="comm_auto_run_idem_uniq")),
        migrations.AddConstraint(model_name="communicationpreference", constraint=models.UniqueConstraint(fields=("owner", "patient"), name="comm_preference_patient_uniq")),
        migrations.AddIndex(model_name="communicationpreference", index=models.Index(fields=["owner", "patient"], name="comm_pref_owner_patient_idx")),
        migrations.AddIndex(model_name="inappnotification", index=models.Index(fields=["recipient", "is_read", "created_at"], name="comm_notification_unread_idx")),
        migrations.AddConstraint(model_name="inboundmessage", constraint=models.UniqueConstraint(fields=("provider", "external_id"), name="comm_inbound_external_uniq")),
        migrations.AddConstraint(model_name="communicationchannelconfig", constraint=models.UniqueConstraint(fields=("owner", "channel"), name="comm_channel_owner_uniq")),
        migrations.AddIndex(model_name="publiccommunicationactiontoken", index=models.Index(fields=["purpose", "expires_at"], name="comm_token_expiry_idx")),
    ]
