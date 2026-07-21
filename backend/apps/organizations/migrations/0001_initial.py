# Generated for the additive multi-tenant expansion phase.

import decimal
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Organization",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=160)),
                ("slug", models.SlugField(max_length=180, unique=True)),
                ("legal_name", models.CharField(blank=True, max_length=200)),
                ("organization_type", models.CharField(choices=[("individual", "Profissional individual"), ("clinic", "Clínica"), ("company", "Empresa")], db_index=True, default="individual", max_length=20)),
                ("document", models.CharField(blank=True, max_length=32)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=24)),
                ("timezone", models.CharField(default="America/Sao_Paulo", max_length=64)),
                ("status", models.CharField(choices=[("active", "Ativa"), ("suspended", "Suspensa"), ("archived", "Arquivada")], db_index=True, default="active", max_length=20)),
                ("onboarding_status", models.CharField(choices=[("pending", "Pendente"), ("in_progress", "Em andamento"), ("completed", "Concluído")], db_index=True, default="pending", max_length=20)),
                ("onboarding_step", models.PositiveSmallIntegerField(default=1)),
                ("onboarding_completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_organizations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="OrganizationMembership",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("role", models.CharField(choices=[("owner", "Proprietário"), ("admin", "Administrador"), ("therapist", "Terapeuta"), ("receptionist", "Recepcionista"), ("finance", "Financeiro"), ("viewer", "Somente leitura")], max_length=20)),
                ("status", models.CharField(choices=[("invited", "Convidado"), ("active", "Ativo"), ("suspended", "Suspenso"), ("revoked", "Revogado")], db_index=True, default="active", max_length=20)),
                ("is_default", models.BooleanField(default=False)),
                ("joined_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("invited_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="organization_memberships_invited", to=settings.AUTH_USER_MODEL)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="organizations.organization")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="organization_memberships", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["organization__name", "user__full_name"]},
        ),
        migrations.CreateModel(
            name="OrganizationInvitation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("email", models.EmailField(max_length=254)),
                ("role", models.CharField(choices=[("owner", "Proprietário"), ("admin", "Administrador"), ("therapist", "Terapeuta"), ("receptionist", "Recepcionista"), ("finance", "Financeiro"), ("viewer", "Somente leitura")], max_length=20)),
                ("status", models.CharField(choices=[("pending", "Pendente"), ("accepted", "Aceito"), ("revoked", "Revogado"), ("expired", "Expirado")], db_index=True, default="pending", max_length=20)),
                ("token_hash", models.CharField(editable=False, max_length=64, unique=True)),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("accepted_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("accepted_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="organization_invitations_accepted", to=settings.AUTH_USER_MODEL)),
                ("invited_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="organization_invitations_sent", to=settings.AUTH_USER_MODEL)),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="invitations", to="organizations.organization")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="OrganizationSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("default_timezone", models.CharField(default="America/Sao_Paulo", max_length=64)),
                ("default_currency", models.CharField(default="BRL", max_length=3)),
                ("default_appointment_duration", models.PositiveSmallIntegerField(default=50)),
                ("minimum_booking_notice_minutes", models.PositiveIntegerField(default=0)),
                ("maximum_booking_days", models.PositiveSmallIntegerField(default=90)),
                ("cancellation_notice_hours", models.PositiveSmallIntegerField(default=24)),
                ("allow_online_booking", models.BooleanField(default=False)),
                ("allow_patient_portal", models.BooleanField(default=False)),
                ("allow_telemedicine", models.BooleanField(default=False)),
                ("send_appointment_reminders", models.BooleanField(default=True)),
                ("reminder_hours_before", models.PositiveSmallIntegerField(default=24)),
                ("business_name_on_documents", models.CharField(blank=True, max_length=180)),
                ("document_header", models.TextField(blank=True)),
                ("document_footer", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("organization", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="settings", to="organizations.organization")),
            ],
            options={"verbose_name": "Configurações da organização", "verbose_name_plural": "Configurações das organizações"},
        ),
        migrations.CreateModel(
            name="ProfessionalProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(blank=True, max_length=160)),
                ("professional_title", models.CharField(blank=True, max_length=120)),
                ("council_type", models.CharField(blank=True, max_length=40)),
                ("council_number", models.CharField(blank=True, max_length=40)),
                ("council_region", models.CharField(blank=True, max_length=20)),
                ("specialties", models.JSONField(blank=True, default=list)),
                ("bio", models.TextField(blank=True)),
                ("phone", models.CharField(blank=True, max_length=24)),
                ("public_email", models.EmailField(blank=True, max_length=254)),
                ("default_appointment_duration", models.PositiveSmallIntegerField(default=50)),
                ("default_session_value", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=10)),
                ("accepts_online", models.BooleanField(default=False)),
                ("accepts_in_person", models.BooleanField(default=True)),
                ("is_public", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("membership", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="professional_profile", to="organizations.organizationmembership")),
            ],
            options={"ordering": ["membership__user__full_name"]},
        ),
        migrations.AddIndex(model_name="organization", index=models.Index(fields=["slug"], name="org_slug_idx")),
        migrations.AddIndex(model_name="organization", index=models.Index(fields=["status"], name="org_status_idx")),
        migrations.AddIndex(model_name="organization", index=models.Index(fields=["created_by"], name="org_created_by_idx")),
        migrations.AddIndex(model_name="organization", index=models.Index(fields=["created_at"], name="org_created_at_idx")),
        migrations.AddConstraint(model_name="organizationmembership", constraint=models.UniqueConstraint(fields=("organization", "user"), name="org_membership_unique_user")),
        migrations.AddConstraint(model_name="organizationmembership", constraint=models.UniqueConstraint(condition=models.Q(("is_default", True)), fields=("user",), name="org_membership_one_default")),
        migrations.AddIndex(model_name="organizationmembership", index=models.Index(fields=["organization", "status"], name="org_member_org_status_idx")),
        migrations.AddIndex(model_name="organizationmembership", index=models.Index(fields=["user", "status"], name="org_member_user_status_idx")),
        migrations.AddIndex(model_name="organizationmembership", index=models.Index(fields=["organization", "role"], name="org_member_org_role_idx")),
        migrations.AddConstraint(model_name="organizationinvitation", constraint=models.UniqueConstraint(condition=models.Q(("status", "pending")), fields=("organization", "email"), name="org_invite_unique_pending_email")),
        migrations.AddIndex(model_name="organizationinvitation", index=models.Index(fields=["organization", "status"], name="org_invite_org_status_idx")),
        migrations.AddIndex(model_name="organizationinvitation", index=models.Index(fields=["email", "status"], name="org_invite_email_status_idx")),
    ]
