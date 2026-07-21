import django.db.models.deletion
from django.db import migrations, models


def _membership_organization_id(Membership, user_id):
    memberships = Membership.objects.filter(user_id=user_id, status="active")
    default_id = (
        memberships.filter(is_default=True)
        .values_list("organization_id", flat=True)
        .first()
    )
    if default_id:
        return default_id
    first_two = list(
        memberships.order_by("created_at").values_list("organization_id", flat=True)[:2]
    )
    return first_two[0] if len(first_two) == 1 else None


def backfill_financial_organizations(apps, schema_editor):
    FinancialTransaction = apps.get_model("financeiro", "FinancialTransaction")
    MonthlySubscription = apps.get_model("financeiro", "MonthlySubscription")
    Membership = apps.get_model("organizations", "OrganizationMembership")

    subscriptions = MonthlySubscription.objects.filter(organization__isnull=True).select_related(
        "patient"
    )
    for item in subscriptions.iterator(chunk_size=500):
        organization_id = getattr(item.patient, "organization_id", None)
        if organization_id is None:
            organization_id = _membership_organization_id(Membership, item.therapist_id)
        if organization_id is not None:
            MonthlySubscription.objects.filter(pk=item.pk, organization__isnull=True).update(
                organization_id=organization_id
            )

    transactions = FinancialTransaction.objects.filter(organization__isnull=True).select_related(
        "appointment",
        "patient",
        "subscription",
    )
    for item in transactions.iterator(chunk_size=500):
        organization_id = None
        if item.appointment_id:
            organization_id = getattr(item.appointment, "organization_id", None)
        if organization_id is None and item.patient_id:
            organization_id = getattr(item.patient, "organization_id", None)
        if organization_id is None and item.subscription_id:
            organization_id = getattr(item.subscription, "organization_id", None)
        if organization_id is None:
            organization_id = _membership_organization_id(Membership, item.therapist_id)
        if organization_id is not None:
            FinancialTransaction.objects.filter(
                pk=item.pk,
                organization__isnull=True,
            ).update(organization_id=organization_id)

    missing_subscriptions = MonthlySubscription.objects.filter(
        organization__isnull=True
    ).count()
    missing_transactions = FinancialTransaction.objects.filter(
        organization__isnull=True
    ).count()
    if missing_subscriptions or missing_transactions:
        raise RuntimeError(
            "Backfill financeiro incompleto: "
            f"mensalidades={missing_subscriptions}, transações={missing_transactions}."
        )


def clear_financial_organizations(apps, schema_editor):
    apps.get_model("financeiro", "FinancialTransaction").objects.update(
        organization=None
    )
    apps.get_model("financeiro", "MonthlySubscription").objects.update(
        organization=None
    )


class Migration(migrations.Migration):
    dependencies = [
        ("financeiro", "0011_unique_appointment_source"),
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="financialtransaction",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="financial_transactions",
                to="organizations.organization",
                verbose_name="Organização",
            ),
        ),
        migrations.AddField(
            model_name="monthlysubscription",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="monthly_subscriptions",
                to="organizations.organization",
                verbose_name="Organização",
            ),
        ),
        migrations.RunPython(
            backfill_financial_organizations,
            clear_financial_organizations,
        ),
        migrations.AlterField(
            model_name="financialtransaction",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="financial_transactions",
                to="organizations.organization",
                verbose_name="Organização",
            ),
        ),
        migrations.AlterField(
            model_name="monthlysubscription",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="monthly_subscriptions",
                to="organizations.organization",
                verbose_name="Organização",
            ),
        ),
        migrations.AddIndex(
            model_name="financialtransaction",
            index=models.Index(
                fields=["organization", "payment_status"],
                name="fin_org_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="financialtransaction",
            index=models.Index(
                fields=["organization", "created_at"],
                name="fin_org_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="financialtransaction",
            index=models.Index(
                fields=["organization", "due_date"],
                name="fin_org_due_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="monthlysubscription",
            index=models.Index(
                fields=["organization", "status"],
                name="fin_sub_org_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="monthlysubscription",
            index=models.Index(
                fields=["organization", "next_billing_date"],
                name="fin_sub_org_bill_idx",
            ),
        ),
    ]
