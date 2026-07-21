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


def backfill_document_organizations(apps, schema_editor):
    DocumentTemplate = apps.get_model("documents", "DocumentTemplate")
    GeneratedDocument = apps.get_model("documents", "GeneratedDocument")
    DocumentSequence = apps.get_model("documents", "DocumentSequence")
    Membership = apps.get_model("organizations", "OrganizationMembership")

    for item in DocumentTemplate.objects.filter(
        is_library_template=False,
        organization__isnull=True,
    ).iterator(chunk_size=500):
        organization_id = _membership_organization_id(Membership, item.owner_id)
        if organization_id:
            DocumentTemplate.objects.filter(pk=item.pk).update(
                organization_id=organization_id
            )

    generated = GeneratedDocument.objects.filter(
        organization__isnull=True
    ).select_related("patient")
    for item in generated.iterator(chunk_size=500):
        organization_id = getattr(item.patient, "organization_id", None)
        if organization_id is None:
            organization_id = _membership_organization_id(Membership, item.owner_id)
        if organization_id:
            GeneratedDocument.objects.filter(pk=item.pk).update(
                organization_id=organization_id
            )

    for item in DocumentSequence.objects.filter(
        organization__isnull=True
    ).iterator(chunk_size=500):
        organization_id = _membership_organization_id(Membership, item.owner_id)
        if organization_id:
            DocumentSequence.objects.filter(pk=item.pk).update(
                organization_id=organization_id
            )

    missing_templates = DocumentTemplate.objects.filter(
        is_library_template=False,
        organization__isnull=True,
    ).count()
    missing_generated = GeneratedDocument.objects.filter(
        organization__isnull=True
    ).count()
    missing_sequences = DocumentSequence.objects.filter(
        organization__isnull=True
    ).count()
    if missing_templates or missing_generated or missing_sequences:
        raise RuntimeError(
            "Backfill documental incompleto: "
            f"templates={missing_templates}, documentos={missing_generated}, "
            f"sequências={missing_sequences}."
        )


def clear_document_organizations(apps, schema_editor):
    apps.get_model("documents", "DocumentTemplate").objects.filter(
        is_library_template=False
    ).update(organization=None)
    apps.get_model("documents", "GeneratedDocument").objects.update(
        organization=None
    )
    apps.get_model("documents", "DocumentSequence").objects.update(
        organization=None
    )


class Migration(migrations.Migration):
    dependencies = [
        ("documents", "0002_seed_library"),
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="documenttemplate",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="document_templates",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="generateddocument",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="generated_documents",
                to="organizations.organization",
            ),
        ),
        migrations.AddField(
            model_name="documentsequence",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="document_sequences",
                to="organizations.organization",
            ),
        ),
        migrations.RunPython(
            backfill_document_organizations,
            clear_document_organizations,
        ),
        migrations.AlterField(
            model_name="generateddocument",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="generated_documents",
                to="organizations.organization",
            ),
        ),
        migrations.AlterField(
            model_name="documentsequence",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="document_sequences",
                to="organizations.organization",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="documenttemplate",
            name="unique_active_document_template_owner_name",
        ),
        migrations.RemoveConstraint(
            model_name="documenttemplate",
            name="unique_active_library_template_name",
        ),
        migrations.RemoveConstraint(
            model_name="documenttemplate",
            name="document_template_scope_consistent",
        ),
        migrations.RemoveConstraint(
            model_name="generateddocument",
            name="unique_generated_document_number_owner",
        ),
        migrations.RemoveConstraint(
            model_name="generateddocument",
            name="unique_generated_document_idempotency_owner",
        ),
        migrations.RemoveConstraint(
            model_name="documentsequence",
            name="unique_document_sequence_owner_year",
        ),
        migrations.AddIndex(
            model_name="documenttemplate",
            index=models.Index(
                fields=["organization", "status"],
                name="doc_tpl_org_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="generateddocument",
            index=models.Index(
                fields=["organization", "status"],
                name="gen_doc_org_status_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="documenttemplate",
            constraint=models.UniqueConstraint(
                fields=("organization", "name"),
                condition=Q(
                    archived_at__isnull=True,
                    organization__isnull=False,
                    is_library_template=False,
                ),
                name="unique_active_document_template_org_name",
            ),
        ),
        migrations.AddConstraint(
            model_name="documenttemplate",
            constraint=models.UniqueConstraint(
                fields=("name",),
                condition=Q(
                    organization__isnull=True,
                    owner__isnull=True,
                    is_library_template=True,
                    archived_at__isnull=True,
                ),
                name="unique_active_library_template_name",
            ),
        ),
        migrations.AddConstraint(
            model_name="documenttemplate",
            constraint=models.CheckConstraint(
                condition=(
                    Q(
                        is_library_template=False,
                        organization__isnull=False,
                        owner__isnull=False,
                    )
                    | Q(
                        is_library_template=True,
                        organization__isnull=True,
                        owner__isnull=True,
                    )
                ),
                name="document_template_scope_consistent",
            ),
        ),
        migrations.AddConstraint(
            model_name="generateddocument",
            constraint=models.UniqueConstraint(
                fields=("organization", "document_number"),
                name="unique_generated_document_number_org",
            ),
        ),
        migrations.AddConstraint(
            model_name="generateddocument",
            constraint=models.UniqueConstraint(
                fields=("organization", "idempotency_key"),
                condition=Q(idempotency_key__isnull=False),
                name="unique_generated_document_idempotency_org",
            ),
        ),
        migrations.AddConstraint(
            model_name="documentsequence",
            constraint=models.UniqueConstraint(
                fields=("organization", "year"),
                name="unique_document_sequence_org_year",
            ),
        ),
    ]
