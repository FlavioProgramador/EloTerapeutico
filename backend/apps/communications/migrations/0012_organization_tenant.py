import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


def _membership_organization_id(Membership, user_id):
    if not user_id:
        return None
    memberships = Membership.objects.filter(user_id=user_id, status="active")
    default_id = memberships.filter(is_default=True).values_list(
        "organization_id",
        flat=True,
    ).first()
    if default_id:
        return default_id
    first_two = list(
        memberships.order_by("created_at").values_list("organization_id", flat=True)[:2]
    )
    return first_two[0] if len(first_two) == 1 else None


def backfill_communication_organizations(apps, schema_editor):
    Communication = apps.get_model("communications", "Communication")
    Template = apps.get_model("communications", "CommunicationTemplate")
    Automation = apps.get_model("communications", "CommunicationAutomation")
    Channel = apps.get_model("communications", "CommunicationChannelConfig")
    Preference = apps.get_model("communications", "CommunicationPreference")
    Notification = apps.get_model("communications", "InAppNotification")
    Inbound = apps.get_model("communications", "InboundMessage")
    Membership = apps.get_model("organizations", "OrganizationMembership")

    for item in Template.objects.filter(
        is_system_template=False,
        organization__isnull=True,
    ).iterator(chunk_size=500):
        organization_id = _membership_organization_id(Membership, item.owner_id)
        if organization_id:
            Template.objects.filter(pk=item.pk).update(organization_id=organization_id)

    communications = Communication.objects.filter(
        organization__isnull=True
    ).select_related(
        "patient",
        "appointment",
        "form_submission",
        "document",
        "financial_transaction",
        "template",
    )
    for item in communications.iterator(chunk_size=500):
        organization_id = None
        for relation_name in (
            "patient",
            "appointment",
            "form_submission",
            "document",
            "financial_transaction",
            "template",
        ):
            relation_id = getattr(item, f"{relation_name}_id", None)
            if relation_id:
                organization_id = getattr(
                    getattr(item, relation_name),
                    "organization_id",
                    None,
                )
                if organization_id:
                    break
        if organization_id is None:
            organization_id = _membership_organization_id(Membership, item.owner_id)
        if organization_id:
            Communication.objects.filter(pk=item.pk).update(
                organization_id=organization_id
            )

    for item in Automation.objects.filter(
        organization__isnull=True
    ).select_related("template").iterator(chunk_size=500):
        organization_id = getattr(item.template, "organization_id", None)
        if organization_id is None:
            organization_id = _membership_organization_id(Membership, item.owner_id)
        if organization_id:
            Automation.objects.filter(pk=item.pk).update(organization_id=organization_id)

    for item in Channel.objects.filter(
        organization__isnull=True
    ).iterator(chunk_size=500):
        organization_id = _membership_organization_id(Membership, item.owner_id)
        if organization_id:
            Channel.objects.filter(pk=item.pk).update(organization_id=organization_id)

    for item in Preference.objects.filter(
        organization__isnull=True
    ).select_related("patient").iterator(chunk_size=500):
        organization_id = getattr(item.patient, "organization_id", None)
        if organization_id:
            Preference.objects.filter(pk=item.pk).update(organization_id=organization_id)

    notifications = Notification.objects.filter(
        organization__isnull=True
    ).select_related("communication")
    for item in notifications.iterator(chunk_size=500):
        organization_id = getattr(item.communication, "organization_id", None)
        if organization_id is None:
            organization_id = _membership_organization_id(
                Membership,
                item.recipient_id or item.owner_id,
            )
        if organization_id:
            Notification.objects.filter(pk=item.pk).update(
                organization_id=organization_id
            )

    inbound = Inbound.objects.filter(organization__isnull=True).select_related(
        "patient",
        "communication",
    )
    for item in inbound.iterator(chunk_size=500):
        organization_id = getattr(item.patient, "organization_id", None)
        if organization_id is None:
            organization_id = getattr(item.communication, "organization_id", None)
        if organization_id is None:
            organization_id = _membership_organization_id(Membership, item.owner_id)
        if organization_id:
            Inbound.objects.filter(pk=item.pk).update(organization_id=organization_id)

    missing = {
        "templates": Template.objects.filter(
            is_system_template=False,
            organization__isnull=True,
        ).count(),
        "communications": Communication.objects.filter(organization__isnull=True).count(),
        "automations": Automation.objects.filter(organization__isnull=True).count(),
        "channels": Channel.objects.filter(organization__isnull=True).count(),
        "preferences": Preference.objects.filter(organization__isnull=True).count(),
        "notifications": Notification.objects.filter(organization__isnull=True).count(),
        "inbound": Inbound.objects.filter(organization__isnull=True).count(),
    }
    if any(missing.values()):
        raise RuntimeError(f"Backfill de comunicações incompleto: {missing}.")


def clear_communication_organizations(apps, schema_editor):
    for model_name in (
        "Communication",
        "CommunicationAutomation",
        "CommunicationChannelConfig",
        "CommunicationPreference",
        "InAppNotification",
        "InboundMessage",
    ):
        apps.get_model("communications", model_name).objects.update(organization=None)
    apps.get_model("communications", "CommunicationTemplate").objects.filter(
        is_system_template=False
    ).update(organization=None)


class Migration(migrations.Migration):
    dependencies = [
        ("communications", "0011_notification_center"),
        ("organizations", "0001_initial"),
        ("forms", "0002_organization_tenant"),
        ("documents", "0003_organization_tenant"),
        ("financeiro", "0012_organization_tenant"),
    ]

    operations = [
        migrations.AddField(
            model_name="communication",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="communications",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="communicationtemplate",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="communication_templates",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="communicationautomation",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="communication_automations",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="communicationchannelconfig",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="communication_channel_configs",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="communicationpreference",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="communication_preferences",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="inappnotification",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="in_app_notifications",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="inboundmessage",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="inbound_messages",
                to="organizations.organization",
            ),
        ),
        migrations.RunPython(
            backfill_communication_organizations,
            clear_communication_organizations,
        ),
        migrations.AlterField(
            model_name="communication",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="communications",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="communicationautomation",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="communication_automations",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="communicationchannelconfig",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="communication_channel_configs",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="communicationpreference",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="communication_preferences",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="inappnotification",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="in_app_notifications",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="inboundmessage",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="inbound_messages",
                to="organizations.organization",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="communication",
            name="comm_owner_idempotency_uniq",
        ),
        migrations.RemoveConstraint(
            model_name="communicationtemplate",
            name="comm_template_owner_slug_uniq",
        ),
        migrations.RemoveConstraint(
            model_name="communicationtemplate",
            name="comm_system_template_slug_uniq",
        ),
        migrations.RemoveConstraint(
            model_name="communicationtemplate",
            name="comm_system_template_without_owner",
        ),
        migrations.RemoveConstraint(
            model_name="communicationchannelconfig",
            name="comm_channel_owner_uniq",
        ),
        migrations.RemoveConstraint(
            model_name="communicationpreference",
            name="comm_preference_patient_uniq",
        ),
        migrations.RemoveConstraint(
            model_name="inboundmessage",
            name="comm_inbound_external_uniq",
        ),
        migrations.AddConstraint(
            model_name="communication",
            constraint=models.UniqueConstraint(
                fields=("organization", "idempotency_key"),
                name="comm_org_idempotency_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="communicationtemplate",
            constraint=models.UniqueConstraint(
                fields=("organization", "slug", "channel"),
                condition=Q(
                    is_system_template=False,
                    organization__isnull=False,
                ),
                name="comm_template_org_slug_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="communicationtemplate",
            constraint=models.UniqueConstraint(
                fields=("slug", "channel"),
                condition=Q(
                    is_system_template=True,
                    organization__isnull=True,
                    owner__isnull=True,
                ),
                name="comm_system_template_slug_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="communicationtemplate",
            constraint=models.CheckConstraint(
                condition=(
                    Q(
                        is_system_template=True,
                        organization__isnull=True,
                        owner__isnull=True,
                    )
                    | Q(
                        is_system_template=False,
                        organization__isnull=False,
                        owner__isnull=False,
                    )
                ),
                name="comm_template_scope_consistent",
            ),
        ),
        migrations.AddConstraint(
            model_name="communicationchannelconfig",
            constraint=models.UniqueConstraint(
                fields=("organization", "channel"),
                name="comm_channel_org_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="communicationpreference",
            constraint=models.UniqueConstraint(
                fields=("organization", "patient"),
                name="comm_preference_org_patient_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="inboundmessage",
            constraint=models.UniqueConstraint(
                fields=("organization", "provider", "external_id"),
                name="comm_inbound_org_external_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="communication",
            index=models.Index(fields=["organization", "status"], name="comm_org_status_idx"),
        ),
        migrations.AddIndex(
            model_name="communication",
            index=models.Index(fields=["organization", "channel"], name="comm_org_channel_idx"),
        ),
        migrations.AddIndex(
            model_name="communication",
            index=models.Index(fields=["organization", "patient"], name="comm_org_patient_idx"),
        ),
        migrations.AddIndex(
            model_name="communicationtemplate",
            index=models.Index(
                fields=["organization", "is_active", "is_archived"],
                name="comm_template_org_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="communicationautomation",
            index=models.Index(
                fields=["organization", "is_active", "event_type"],
                name="comm_auto_org_event_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="communicationchannelconfig",
            index=models.Index(
                fields=["organization", "is_active", "connection_status"],
                name="comm_channel_org_oper_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="communicationpreference",
            index=models.Index(
                fields=["organization", "patient"],
                name="comm_pref_org_patient_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="inappnotification",
            index=models.Index(
                fields=["organization", "recipient", "is_read", "created_at"],
                name="comm_notif_org_unread_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="inboundmessage",
            index=models.Index(
                fields=["organization", "status", "received_at"],
                name="comm_inbound_org_status_idx",
            ),
        ),
    ]
