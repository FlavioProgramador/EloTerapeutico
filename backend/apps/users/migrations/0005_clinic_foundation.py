import uuid

import apps.core.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_authsession"),
    ]

    operations = [
        migrations.CreateModel(
            name="Clinic",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "public_id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                        verbose_name="Identificador público",
                    ),
                ),
                ("name", models.CharField(max_length=160, verbose_name="Nome da clínica")),
                (
                    "legal_name",
                    models.CharField(blank=True, max_length=200, verbose_name="Razão social"),
                ),
                (
                    "document",
                    models.CharField(
                        blank=True,
                        help_text="Armazene somente quando houver finalidade e base legal definidas.",
                        max_length=32,
                        verbose_name="Documento",
                    ),
                ),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="E-mail")),
                (
                    "phone",
                    models.CharField(
                        blank=True,
                        max_length=20,
                        validators=[apps.core.validators.validate_phone],
                        verbose_name="Telefone",
                    ),
                ),
                (
                    "timezone",
                    models.CharField(
                        default="America/Sao_Paulo",
                        max_length=64,
                        verbose_name="Fuso horário",
                    ),
                ),
                (
                    "logo",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="clinics/logos/",
                        verbose_name="Logotipo",
                    ),
                ),
                ("address", models.JSONField(blank=True, default=dict, verbose_name="Endereço")),
                (
                    "settings",
                    models.JSONField(blank=True, default=dict, verbose_name="Configurações"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Ativa"),
                            ("suspended", "Suspensa"),
                            ("archived", "Arquivada"),
                        ],
                        db_index=True,
                        default="active",
                        max_length=16,
                        verbose_name="Status",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criada em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizada em")),
            ],
            options={
                "verbose_name": "Clínica",
                "verbose_name_plural": "Clínicas",
                "ordering": ["name", "id"],
            },
        ),
        migrations.CreateModel(
            name="ClinicMembership",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "public_id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                        verbose_name="Identificador público",
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("owner", "Proprietário"),
                            ("admin", "Administrador da clínica"),
                            ("therapist", "Terapeuta"),
                            ("secretary", "Secretária"),
                            ("financial", "Financeiro"),
                            ("support", "Suporte restrito"),
                        ],
                        max_length=20,
                        verbose_name="Função",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("invited", "Convidado"),
                            ("active", "Ativo"),
                            ("suspended", "Suspenso"),
                            ("revoked", "Revogado"),
                        ],
                        db_index=True,
                        default="active",
                        max_length=16,
                        verbose_name="Status",
                    ),
                ),
                (
                    "extra_permissions",
                    models.JSONField(blank=True, default=list, verbose_name="Permissões adicionais"),
                ),
                ("joined_at", models.DateTimeField(blank=True, null=True, verbose_name="Entrada em")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
                (
                    "clinic",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to="users.clinic",
                        verbose_name="Clínica",
                    ),
                ),
                (
                    "invited_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="clinic_memberships_invited",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Convidado por",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="clinic_memberships",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Usuário",
                    ),
                ),
            ],
            options={
                "verbose_name": "Vínculo com clínica",
                "verbose_name_plural": "Vínculos com clínicas",
                "ordering": ["clinic__name", "user_id"],
            },
        ),
        migrations.CreateModel(
            name="ClinicInvitation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "public_id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                        verbose_name="Identificador público",
                    ),
                ),
                ("email", models.EmailField(max_length=254, verbose_name="E-mail convidado")),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("owner", "Proprietário"),
                            ("admin", "Administrador da clínica"),
                            ("therapist", "Terapeuta"),
                            ("secretary", "Secretária"),
                            ("financial", "Financeiro"),
                            ("support", "Suporte restrito"),
                        ],
                        max_length=20,
                        verbose_name="Função",
                    ),
                ),
                (
                    "token_hash",
                    models.CharField(
                        editable=False,
                        max_length=64,
                        unique=True,
                        verbose_name="Hash do token",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendente"),
                            ("accepted", "Aceito"),
                            ("expired", "Expirado"),
                            ("revoked", "Revogado"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=16,
                        verbose_name="Status",
                    ),
                ),
                ("expires_at", models.DateTimeField(db_index=True, verbose_name="Expira em")),
                ("accepted_at", models.DateTimeField(blank=True, null=True, verbose_name="Aceito em")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Criado em")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Atualizado em")),
                (
                    "accepted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="clinic_invitations_accepted",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Aceito por",
                    ),
                ),
                (
                    "clinic",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invitations",
                        to="users.clinic",
                        verbose_name="Clínica",
                    ),
                ),
                (
                    "invited_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="clinic_invitations_sent",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Convidado por",
                    ),
                ),
            ],
            options={
                "verbose_name": "Convite de clínica",
                "verbose_name_plural": "Convites de clínica",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddField(
            model_name="authsession",
            name="active_clinic",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="auth_sessions",
                to="users.clinic",
                verbose_name="Clínica ativa",
            ),
        ),
        migrations.AddIndex(
            model_name="clinic",
            index=models.Index(
                fields=["status", "name"],
                name="users_clinic_status_name_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="clinicmembership",
            index=models.Index(
                fields=["user", "status", "clinic"],
                name="users_clinic_member_active_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="clinicmembership",
            index=models.Index(
                fields=["clinic", "role", "status"],
                name="users_clinic_member_role_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="clinicmembership",
            constraint=models.UniqueConstraint(
                fields=("clinic", "user"),
                name="users_clinic_membership_unique",
            ),
        ),
        migrations.AddIndex(
            model_name="clinicinvitation",
            index=models.Index(
                fields=["clinic", "status", "expires_at"],
                name="users_clinic_inv_pend_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="clinicinvitation",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "pending")),
                fields=("clinic", "email"),
                name="users_clinic_pend_inv_unique",
            ),
        ),
        migrations.AddIndex(
            model_name="authsession",
            index=models.Index(
                fields=["active_clinic", "revoked_at"],
                name="users_auths_clinic_active_idx",
            ),
        ),
    ]
