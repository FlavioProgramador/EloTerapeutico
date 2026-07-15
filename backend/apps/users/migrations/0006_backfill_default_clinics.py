from django.db import migrations, transaction
from django.utils import timezone


def _default_name(user):
    configured = str(getattr(user, "clinic_name", "") or "").strip()
    if configured:
        return configured[:160]
    display_name = str(getattr(user, "full_name", "") or "Profissional").strip()
    return f"Clínica de {display_name}"[:160]


def backfill_default_clinics(apps, schema_editor):
    del schema_editor
    User = apps.get_model("users", "User")
    Clinic = apps.get_model("users", "Clinic")
    Membership = apps.get_model("users", "ClinicMembership")
    AuthSession = apps.get_model("users", "AuthSession")

    eligible_users = User.objects.filter(
        is_active=True,
        role__in=["therapist", "admin"],
    ).order_by("pk")

    for user_id in eligible_users.values_list("pk", flat=True).iterator(chunk_size=200):
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user_id)
            membership = (
                Membership.objects.select_related("clinic")
                .filter(
                    user_id=user.pk,
                    status="active",
                    clinic__status="active",
                )
                .order_by("pk")
                .first()
            )
            if membership is None:
                clinic = Clinic.objects.create(
                    name=_default_name(user),
                    email=user.email,
                    phone=user.phone,
                    address=user.professional_address or {},
                    timezone="America/Sao_Paulo",
                    status="active",
                )
                membership = Membership.objects.create(
                    clinic_id=clinic.pk,
                    user_id=user.pk,
                    role="owner",
                    status="active",
                    joined_at=timezone.now(),
                )

            AuthSession.objects.filter(
                user_id=user.pk,
                active_clinic_id__isnull=True,
                revoked_at__isnull=True,
                expires_at__gt=timezone.now(),
            ).update(active_clinic_id=membership.clinic_id)


def noop_reverse(apps, schema_editor):
    del apps, schema_editor
    # Não remove clínicas ou vínculos para evitar perda de dados no rollback.


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("users", "0005_clinic_foundation"),
    ]

    operations = [
        migrations.RunPython(backfill_default_clinics, noop_reverse),
    ]
