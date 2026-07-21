import django.db.models.deletion
from django.db import migrations, models


def backfill_audit_organizations(apps, schema_editor):
    AuditLog = apps.get_model("audit", "AuditLog")
    Membership = apps.get_model("organizations", "OrganizationMembership")
    for user_id in AuditLog.objects.filter(
        organization__isnull=True,
        user__isnull=False,
    ).values_list("user_id", flat=True).distinct():
        membership = (
            Membership.objects.filter(user_id=user_id, status="active")
            .order_by("-is_default", "created_at")
            .first()
        )
        if membership is not None:
            AuditLog.objects.filter(
                organization__isnull=True,
                user_id=user_id,
            ).update(organization_id=membership.organization_id)


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0001_initial"),
        ("audit", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditlog",
            name="organization",
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="audit_logs",
                to="organizations.organization",
                verbose_name="Organização",
            ),
        ),
        migrations.RunPython(backfill_audit_organizations, migrations.RunPython.noop),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(fields=["organization", "timestamp"], name="audit_org_timestamp_idx"),
        ),
    ]
