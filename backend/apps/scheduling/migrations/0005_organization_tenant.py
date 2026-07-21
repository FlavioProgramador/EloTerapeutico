import django.db.models.deletion
from django.db import migrations, models


def organization_for_user(apps, user_id):
    Membership = apps.get_model("organizations", "OrganizationMembership")
    membership = (
        Membership.objects.filter(user_id=user_id, status="active")
        .order_by("-is_default", "created_at")
        .first()
    )
    return membership.organization_id if membership else None


def backfill_agenda_organizations(apps, schema_editor):
    Appointment = apps.get_model("agenda", "Appointment")
    AppointmentRecurrence = apps.get_model("agenda", "AppointmentRecurrence")
    Room = apps.get_model("agenda", "Room")
    PatientPackage = apps.get_model("agenda", "PatientPackage")
    ScheduleBlock = apps.get_model("agenda", "ScheduleBlock")
    PackageSession = apps.get_model("agenda", "PackageSession")
    TelemedicineRoom = apps.get_model("agenda", "TelemedicineRoom")
    AppointmentReminder = apps.get_model("agenda", "AppointmentReminder")

    for model in (Appointment, AppointmentRecurrence, PatientPackage):
        for object_id, organization_id in model.objects.filter(
            organization__isnull=True,
            patient__organization__isnull=False,
        ).values_list("pk", "patient__organization_id").iterator(chunk_size=500):
            model.objects.filter(pk=object_id, organization__isnull=True).update(
                organization_id=organization_id
            )

    for model in (Room, ScheduleBlock):
        for object_id, therapist_id in model.objects.filter(
            organization__isnull=True
        ).values_list("pk", "therapist_id").iterator(chunk_size=500):
            organization_id = organization_for_user(apps, therapist_id)
            if organization_id:
                model.objects.filter(pk=object_id, organization__isnull=True).update(
                    organization_id=organization_id
                )

    for object_id, organization_id in PackageSession.objects.filter(
        organization__isnull=True,
        package__organization__isnull=False,
    ).values_list("pk", "package__organization_id").iterator(chunk_size=500):
        PackageSession.objects.filter(pk=object_id, organization__isnull=True).update(
            organization_id=organization_id
        )

    for model in (TelemedicineRoom, AppointmentReminder):
        for object_id, organization_id in model.objects.filter(
            organization__isnull=True,
            appointment__organization__isnull=False,
        ).values_list("pk", "appointment__organization_id").iterator(chunk_size=500):
            model.objects.filter(pk=object_id, organization__isnull=True).update(
                organization_id=organization_id
            )


def assert_no_missing_tenant(apps, schema_editor):
    for model_name in (
        "Appointment",
        "AppointmentRecurrence",
        "Room",
        "PatientPackage",
        "ScheduleBlock",
        "PackageSession",
        "TelemedicineRoom",
        "AppointmentReminder",
    ):
        model = apps.get_model("agenda", model_name)
        missing = model.objects.filter(organization__isnull=True).count()
        if missing:
            raise RuntimeError(
                f"Não foi possível associar {missing} registro(s) de {model_name} a uma organização. "
                "Execute backfill_organizations e revise os dados antes de continuar."
            )


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0001_initial"),
        ("patients", "0010_patient_organization"),
        ("agenda", "0004_agenda_complete_domain"),
    ]

    operations = [
        migrations.AddField(
            model_name="appointment",
            name="organization",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="appointments",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="appointmentrecurrence",
            name="organization",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="appointment_recurrences",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="room",
            name="organization",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="agenda_rooms",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="patientpackage",
            name="organization",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="patient_packages",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="scheduleblock",
            name="organization",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="schedule_blocks",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="packagesession",
            name="organization",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="package_sessions",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="telemedicineroom",
            name="organization",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="telemedicine_rooms",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="appointmentreminder",
            name="organization",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="appointment_reminders",
                to="organizations.organization",
            ),
        ),
        migrations.RunPython(backfill_agenda_organizations, migrations.RunPython.noop),
        migrations.RunPython(assert_no_missing_tenant, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="appointment",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="appointments",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="appointmentrecurrence",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="appointment_recurrences",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="room",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="agenda_rooms",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="patientpackage",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="patient_packages",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="scheduleblock",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="schedule_blocks",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="packagesession",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="package_sessions",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="telemedicineroom",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="telemedicine_rooms",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="appointmentreminder",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="appointment_reminders",
                to="organizations.organization",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="room",
            name="uniq_room_owner_name",
        ),
        migrations.AddConstraint(
            model_name="room",
            constraint=models.UniqueConstraint(
                fields=("organization", "name"),
                name="uniq_room_org_name",
            ),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(fields=["organization", "start_time"], name="appt_org_start_idx"),
        ),
        migrations.AddIndex(
            model_name="appointment",
            index=models.Index(fields=["organization", "status"], name="appt_org_status_idx"),
        ),
        migrations.AddIndex(
            model_name="appointmentrecurrence",
            index=models.Index(fields=["organization", "status"], name="rec_org_status_idx"),
        ),
        migrations.AddIndex(
            model_name="room",
            index=models.Index(fields=["organization", "is_active"], name="room_org_active_idx"),
        ),
        migrations.AddIndex(
            model_name="patientpackage",
            index=models.Index(fields=["organization", "status"], name="pkg_org_status_idx"),
        ),
        migrations.AddIndex(
            model_name="scheduleblock",
            index=models.Index(fields=["organization", "start_time"], name="block_org_start_idx"),
        ),
        migrations.AddIndex(
            model_name="packagesession",
            index=models.Index(fields=["organization", "scheduled_for"], name="pkg_session_org_time_idx"),
        ),
        migrations.AddIndex(
            model_name="telemedicineroom",
            index=models.Index(fields=["organization", "status"], name="telemed_org_status_idx"),
        ),
        migrations.AddIndex(
            model_name="appointmentreminder",
            index=models.Index(
                fields=["organization", "status", "scheduled_for"],
                name="reminder_org_status_idx",
            ),
        ),
    ]
