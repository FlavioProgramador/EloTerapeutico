import uuid

import apps.core.fields.encrypted
import django.conf
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def backfill_room_security(apps, schema_editor):
    TelemedicineRoom = apps.get_model("agenda", "TelemedicineRoom")
    for room in TelemedicineRoom.objects.all().iterator(chunk_size=500):
        room.public_id = uuid.uuid4()
        room.provider_room_name = f"tm_{uuid.uuid4().hex}"
        room.patient_token = None
        room.professional_token = None
        room.save(
            update_fields=[
                "public_id",
                "provider_room_name",
                "patient_token",
                "professional_token",
            ]
        )


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(django.conf.settings.AUTH_USER_MODEL),
        ("agenda", "0005_organization_tenant"),
        ("patients", "0010_patient_organization"),
    ]

    operations = [
        migrations.AddField(
            model_name="telemedicineroom",
            name="public_id",
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name="telemedicineroom",
            name="provider",
            field=models.CharField(default="livekit", max_length=32),
        ),
        migrations.AddField(
            model_name="telemedicineroom",
            name="provider_room_name",
            field=models.CharField(blank=True, max_length=80, null=True, editable=False),
        ),
        migrations.AddField(
            model_name="telemedicineroom",
            name="provider_room_sid",
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AddField(
            model_name="telemedicineroom",
            name="e2ee_key",
            field=apps.core.fields.encrypted.EncryptedTextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="telemedicineroom",
            name="e2ee_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="telemedicineroom",
            name="started_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="telemedicineroom",
            name="ended_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="telemedicineroom",
            name="patient_joined_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="telemedicineroom",
            name="professional_joined_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="telemedicineroom",
            name="last_participant_left_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="telemedicineroom",
            name="closed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="closed_telemedicine_rooms",
                to=django.conf.settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="telemedicineroom",
            name="failure_code",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AlterField(
            model_name="telemedicineroom",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pendente"),
                    ("available", "Disponível"),
                    ("waiting", "Aguardando participante"),
                    ("in_progress", "Em andamento"),
                    ("finished", "Finalizada"),
                    ("cancelled", "Cancelada"),
                    ("expired", "Expirada"),
                    ("failed", "Falhou"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="telemedicineroom",
            name="patient_token",
            field=models.UUIDField(blank=True, editable=False, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="telemedicineroom",
            name="professional_token",
            field=models.UUIDField(blank=True, editable=False, null=True, unique=True),
        ),
        migrations.RunPython(backfill_room_security, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="telemedicineroom",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name="telemedicineroom",
            name="provider_room_name",
            field=models.CharField(max_length=80, unique=True, editable=False),
        ),
        migrations.AddIndex(
            model_name="telemedicineroom",
            index=models.Index(
                fields=["organization", "expires_at"],
                name="telemed_org_expiry_idx",
            ),
        ),
        migrations.CreateModel(
            name="TelemedicineInvitation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("patient", "Paciente")], default="patient", max_length=20)),
                ("token_hash", models.CharField(editable=False, max_length=64, unique=True)),
                ("expires_at", models.DateTimeField()),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                ("use_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_telemedicine_invitations", to=django.conf.settings.AUTH_USER_MODEL)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="telemedicine_invitations", to="organizations.organization")),
                ("room", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="invitations", to="agenda.telemedicineroom")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="TelemedicineConsent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("responsible_guardian_name", models.CharField(blank=True, max_length=180)),
                ("document_version", models.CharField(max_length=32)),
                ("document_hash", models.CharField(max_length=64)),
                ("accepted_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("acceptance_method", models.CharField(choices=[("patient_link", "Link do paciente"), ("responsible_link", "Link do responsável")], default="patient_link", max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="telemedicine_consents", to="organizations.organization")),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="telemedicine_consents", to="patients.patient")),
                ("room", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="consents", to="agenda.telemedicineroom")),
            ],
            options={"ordering": ["-accepted_at"]},
        ),
        migrations.CreateModel(
            name="TelemedicineParticipantSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(choices=[("patient", "Paciente"), ("professional", "Profissional")], max_length=20)),
                ("provider_participant_identity", models.CharField(max_length=180)),
                ("provider_participant_sid", models.CharField(blank=True, max_length=128)),
                ("joined_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("left_at", models.DateTimeField(blank=True, null=True)),
                ("disconnect_reason", models.CharField(blank=True, max_length=64)),
                ("connection_aborted", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="telemedicine_participant_sessions", to="organizations.organization")),
                ("room", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participant_sessions", to="agenda.telemedicineroom")),
            ],
            options={"ordering": ["-joined_at"]},
        ),
        migrations.CreateModel(
            name="TelemedicineWebhookEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("provider", models.CharField(default="livekit", max_length=32)),
                ("provider_event_id", models.CharField(max_length=180)),
                ("event_type", models.CharField(max_length=64)),
                ("occurred_at", models.DateTimeField(blank=True, null=True)),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("payload_hash", models.CharField(max_length=64)),
                ("processing_error", models.CharField(blank=True, max_length=255)),
                ("room", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="webhook_events", to="agenda.telemedicineroom")),
            ],
            options={"ordering": ["-received_at"]},
        ),
        migrations.AddConstraint(
            model_name="telemedicineinvitation",
            constraint=models.UniqueConstraint(condition=models.Q(("revoked_at__isnull", True)), fields=("room", "role"), name="uniq_active_telemed_invite"),
        ),
        migrations.AddIndex(
            model_name="telemedicineinvitation",
            index=models.Index(fields=["organization", "expires_at"], name="telemed_inv_org_exp_idx"),
        ),
        migrations.AddConstraint(
            model_name="telemedicineconsent",
            constraint=models.UniqueConstraint(condition=models.Q(("revoked_at__isnull", True)), fields=("room",), name="uniq_active_telemed_consent"),
        ),
        migrations.AddIndex(
            model_name="telemedicineparticipantsession",
            index=models.Index(fields=["organization", "room", "role"], name="telemed_part_org_room_idx"),
        ),
        migrations.AddConstraint(
            model_name="telemedicinewebhookevent",
            constraint=models.UniqueConstraint(fields=("provider", "provider_event_id"), name="uniq_telemed_provider_event"),
        ),
        migrations.AddIndex(
            model_name="telemedicinewebhookevent",
            index=models.Index(fields=["provider", "event_type", "received_at"], name="telemed_event_type_idx"),
        ),
    ]
