import uuid

import apps.core.validators
import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


def _organization_for_user(apps, user_id):
    Organization = apps.get_model("organizations", "Organization")
    Membership = apps.get_model("organizations", "OrganizationMembership")
    OrganizationSettings = apps.get_model("organizations", "OrganizationSettings")
    ProfessionalProfile = apps.get_model("organizations", "ProfessionalProfile")
    User = apps.get_model("users", "User")

    membership = (
        Membership.objects.filter(user_id=user_id, status="active")
        .order_by("-is_default", "created_at")
        .first()
    )
    if membership is not None:
        return membership.organization_id

    user = User.objects.get(pk=user_id)
    name = f"Consultório de {user.full_name or user.email}"[:160]
    organization = Organization.objects.create(
        name=name,
        slug=f"consultorio-{user_id}-{uuid.uuid4().hex[:8]}",
        organization_type="individual",
        email=user.email,
        phone=getattr(user, "phone", ""),
        timezone=getattr(user, "timezone", "America/Sao_Paulo"),
        status="active",
        onboarding_status="in_progress",
        onboarding_step=1,
        created_by_id=user_id,
    )
    membership = Membership.objects.create(
        organization_id=organization.pk,
        user_id=user_id,
        role="owner",
        status="active",
        is_default=not Membership.objects.filter(user_id=user_id, is_default=True).exists(),
    )
    OrganizationSettings.objects.create(
        organization_id=organization.pk,
        default_timezone=organization.timezone,
        business_name_on_documents=organization.name,
    )
    ProfessionalProfile.objects.create(
        membership_id=membership.pk,
        display_name=getattr(user, "display_name", "") or user.full_name,
        professional_title=getattr(user, "profession", ""),
        council_type="CRP" if getattr(user, "crp_number", "") else "",
        council_number=getattr(user, "crp_number", ""),
        specialties=[getattr(user, "specialty", "")] if getattr(user, "specialty", "") else [],
        bio=getattr(user, "bio", ""),
        phone=getattr(user, "phone", ""),
        public_email=user.email,
        default_appointment_duration=getattr(user, "default_session_duration", 50),
        default_session_value=getattr(user, "default_session_value", 0),
        accepts_online=getattr(user, "default_modality", "") in {"online", "hybrid"},
        accepts_in_person=getattr(user, "default_modality", "in_person") in {"in_person", "hybrid"},
    )
    return organization.pk


def backfill_patient_organizations(apps, schema_editor):
    Patient = apps.get_model("patients", "Patient")
    cache = {}
    queryset = Patient.objects.filter(organization__isnull=True).values_list("pk", "therapist_id")
    for patient_id, therapist_id in queryset.iterator(chunk_size=500):
        if therapist_id not in cache:
            cache[therapist_id] = _organization_for_user(apps, therapist_id)
        Patient.objects.filter(pk=patient_id, organization__isnull=True).update(
            organization_id=cache[therapist_id]
        )


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0001_initial"),
        ("patients", "0009_normalize_patient_tags"),
    ]

    operations = [
        migrations.AddField(
            model_name="patient",
            name="organization",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="patients",
                to="organizations.organization",
                verbose_name="Organização",
            ),
        ),
        migrations.AlterField(
            model_name="patient",
            name="cpf",
            field=models.CharField(
                blank=True,
                max_length=11,
                null=True,
                validators=[apps.core.validators.validate_cpf],
                verbose_name="CPF",
            ),
        ),
        migrations.RunPython(backfill_patient_organizations, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="patient",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="patients",
                to="organizations.organization",
                verbose_name="Organização",
            ),
        ),
        migrations.AddConstraint(
            model_name="patient",
            constraint=models.UniqueConstraint(
                condition=Q(cpf__isnull=False) & ~Q(cpf=""),
                fields=("organization", "cpf"),
                name="patient_org_cpf_uniq",
            ),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(fields=["organization", "therapist"], name="patient_org_therapist_idx"),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(fields=["organization", "status"], name="patient_org_status_idx"),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(fields=["organization", "full_name"], name="patient_org_name_idx"),
        ),
    ]
