import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


def _membership_organization_id(Membership, user_id):
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


def backfill_form_organizations(apps, schema_editor):
    FormTemplate = apps.get_model("forms", "FormTemplate")
    TherapeuticForm = apps.get_model("forms", "TherapeuticForm")
    FormSubmission = apps.get_model("forms", "FormSubmission")
    Membership = apps.get_model("organizations", "OrganizationMembership")

    for item in TherapeuticForm.objects.filter(
        organization__isnull=True
    ).iterator(chunk_size=500):
        organization_id = _membership_organization_id(Membership, item.owner_id)
        if organization_id:
            TherapeuticForm.objects.filter(pk=item.pk).update(
                organization_id=organization_id
            )

    custom_templates = FormTemplate.objects.filter(
        is_system_template=False,
        organization__isnull=True,
    )
    for template in custom_templates.iterator(chunk_size=500):
        organization_ids = list(
            TherapeuticForm.objects.filter(source_template_id=template.pk)
            .exclude(organization__isnull=True)
            .values_list("organization_id", flat=True)
            .distinct()[:2]
        )
        if len(organization_ids) == 1:
            FormTemplate.objects.filter(pk=template.pk).update(
                organization_id=organization_ids[0]
            )

    submissions = FormSubmission.objects.filter(
        organization__isnull=True
    ).select_related("form", "patient", "appointment")
    for item in submissions.iterator(chunk_size=500):
        organization_id = getattr(item.form, "organization_id", None)
        if organization_id is None and item.patient_id:
            organization_id = getattr(item.patient, "organization_id", None)
        if organization_id is None and item.appointment_id:
            organization_id = getattr(item.appointment, "organization_id", None)
        if organization_id is None:
            organization_id = _membership_organization_id(Membership, item.owner_id)
        if organization_id:
            FormSubmission.objects.filter(pk=item.pk).update(
                organization_id=organization_id
            )

    missing_templates = FormTemplate.objects.filter(
        is_system_template=False,
        organization__isnull=True,
    ).count()
    missing_forms = TherapeuticForm.objects.filter(
        organization__isnull=True
    ).count()
    missing_submissions = FormSubmission.objects.filter(
        organization__isnull=True
    ).count()
    if missing_templates or missing_forms or missing_submissions:
        raise RuntimeError(
            "Backfill de formulários incompleto: "
            f"templates={missing_templates}, formulários={missing_forms}, "
            f"submissões={missing_submissions}."
        )


def clear_form_organizations(apps, schema_editor):
    apps.get_model("forms", "FormTemplate").objects.filter(
        is_system_template=False
    ).update(organization=None)
    apps.get_model("forms", "TherapeuticForm").objects.update(organization=None)
    apps.get_model("forms", "FormSubmission").objects.update(organization=None)


class Migration(migrations.Migration):
    dependencies = [
        ("forms", "0001_initial"),
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="formtemplate",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="form_templates",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="therapeuticform",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="therapeutic_forms",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="formsubmission",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="form_submissions",
                to="organizations.organization",
            ),
        ),
        migrations.RunPython(
            backfill_form_organizations,
            clear_form_organizations,
        ),
        migrations.AlterField(
            model_name="therapeuticform",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="therapeutic_forms",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="formsubmission",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="form_submissions",
                to="organizations.organization",
            ),
        ),
        migrations.AddIndex(
            model_name="formtemplate",
            index=models.Index(
                fields=["organization", "is_active"],
                name="form_tpl_org_active_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="therapeuticform",
            index=models.Index(
                fields=["organization", "status"],
                name="form_org_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="therapeuticform",
            index=models.Index(
                fields=["organization", "category"],
                name="form_org_category_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="formsubmission",
            index=models.Index(
                fields=["organization", "status"],
                name="submission_org_status_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="formtemplate",
            constraint=models.CheckConstraint(
                condition=(
                    Q(is_system_template=True, organization__isnull=True)
                    | Q(is_system_template=False, organization__isnull=False)
                ),
                name="form_template_scope_consistent",
            ),
        ),
        migrations.AddConstraint(
            model_name="formtemplate",
            constraint=models.UniqueConstraint(
                fields=("organization", "name"),
                condition=Q(
                    is_system_template=False,
                    organization__isnull=False,
                ),
                name="unique_custom_form_template_org_name",
            ),
        ),
        migrations.AddConstraint(
            model_name="formtemplate",
            constraint=models.UniqueConstraint(
                fields=("name",),
                condition=Q(
                    is_system_template=True,
                    organization__isnull=True,
                ),
                name="unique_system_form_template_name",
            ),
        ),
    ]
