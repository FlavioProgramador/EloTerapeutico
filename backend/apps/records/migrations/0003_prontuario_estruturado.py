# Generated manually for the structured clinical record refactor.

import apps.core.fields
import django.db.models.deletion
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
import apps.records.treatment_models


class Migration(migrations.Migration):
    dependencies = [
        ("records", "0002_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AnamnesisProfile",
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
                    "reason_for_care",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "physical_health_history",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "mental_health_history",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "previous_treatments",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "habits_and_routine",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                ("sleep", apps.core.fields.EncryptedTextField(blank=True, default="")),
                ("nutrition", apps.core.fields.EncryptedTextField(blank=True, default="")),
                (
                    "family_social_relations",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "academic_history",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "professional_history",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "support_network",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "relevant_events",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "initial_assessment",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "clinical_hypotheses",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "custom_fields",
                    apps.core.fields.EncryptedTextField(blank=True, default="{}"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "anamnesis",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="profile",
                        to="records.anamnesis",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="anamnesis_profiles_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AnamnesisVersion",
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
                ("version", models.PositiveIntegerField()),
                ("snapshot", apps.core.fields.EncryptedTextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "anamnesis",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="versions",
                        to="records.anamnesis",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="anamnesis_versions_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-version"]},
        ),
        migrations.CreateModel(
            name="EvolutionClinicalData",
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
                ("session_time", models.TimeField(blank=True, null=True)),
                (
                    "duration_minutes",
                    models.PositiveSmallIntegerField(
                        default=50,
                        validators=[MinValueValidator(1), MaxValueValidator(600)],
                    ),
                ),
                (
                    "modality",
                    models.CharField(
                        choices=[
                            ("in_person", "Presencial"),
                            ("online", "Online"),
                            ("hybrid", "Híbrido"),
                        ],
                        default="in_person",
                        max_length=20,
                    ),
                ),
                (
                    "appointment_type",
                    models.CharField(
                        choices=[
                            ("individual", "Individual"),
                            ("couple", "Casal"),
                            ("family", "Familiar"),
                            ("group", "Grupo"),
                            ("other", "Outro"),
                        ],
                        default="individual",
                        max_length=20,
                    ),
                ),
                (
                    "emotional_state",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "chief_complaint",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "patient_report",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "therapist_observations",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "interventions",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "perceived_evolution",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                ("homework", apps.core.fields.EncryptedTextField(blank=True, default="")),
                ("referrals", apps.core.fields.EncryptedTextField(blank=True, default="")),
                ("next_steps", apps.core.fields.EncryptedTextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "evolution",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="clinical_data",
                        to="records.evolution",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="evolution_clinical_data_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="EvolutionVersion",
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
                ("version", models.PositiveIntegerField()),
                ("snapshot", apps.core.fields.EncryptedTextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="evolution_versions_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "evolution",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="versions",
                        to="records.evolution",
                    ),
                ),
            ],
            options={"ordering": ["-version"]},
        ),
        migrations.CreateModel(
            name="TreatmentGoal",
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
                ("title", models.CharField(max_length=180)),
                ("description", apps.core.fields.EncryptedTextField(blank=True, default="")),
                ("category", models.CharField(blank=True, max_length=80)),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("low", "Baixa"),
                            ("medium", "Média"),
                            ("high", "Alta"),
                        ],
                        default="medium",
                        max_length=12,
                    ),
                ),
                ("start_date", models.DateField()),
                ("target_date", models.DateField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Em andamento"),
                            ("paused", "Pausada"),
                            ("completed", "Concluída"),
                            ("archived", "Arquivada"),
                        ],
                        db_index=True,
                        default="active",
                        max_length=16,
                    ),
                ),
                (
                    "progress",
                    models.PositiveSmallIntegerField(
                        default=0,
                        validators=[MinValueValidator(0), MaxValueValidator(100)],
                    ),
                ),
                ("strategies", apps.core.fields.EncryptedTextField(blank=True, default="")),
                (
                    "evaluation_criteria",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                (
                    "observations",
                    apps.core.fields.EncryptedTextField(blank=True, default=""),
                ),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("archived_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="treatment_goals_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "evolutions",
                    models.ManyToManyField(
                        blank=True,
                        related_name="treatment_goals",
                        to="records.evolution",
                    ),
                ),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="treatment_goals",
                        to="patients.patient",
                    ),
                ),
            ],
            options={"ordering": ["sort_order", "-priority", "created_at"]},
        ),
        migrations.CreateModel(
            name="ClinicalDocument",
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
                    "category",
                    models.CharField(
                        choices=[
                            ("consent", "Termo de consentimento"),
                            ("report", "Relatório"),
                            ("referral", "Encaminhamento"),
                            ("certificate", "Atestado"),
                            ("assessment", "Avaliação"),
                            ("scale", "Escala ou teste"),
                            ("patient_file", "Documento do paciente"),
                            ("other", "Outro"),
                        ],
                        db_index=True,
                        default="other",
                        max_length=24,
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        upload_to=apps.records.treatment_models.clinical_document_path
                    ),
                ),
                ("original_name", models.CharField(max_length=255)),
                ("description", apps.core.fields.EncryptedTextField(blank=True, default="")),
                ("content_type", models.CharField(max_length=120)),
                ("size_bytes", models.PositiveBigIntegerField()),
                ("checksum", models.CharField(db_index=True, max_length=64)),
                ("version", models.PositiveIntegerField(default=1)),
                ("is_archived", models.BooleanField(db_index=True, default=False)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "evolution",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="documents",
                        to="records.evolution",
                    ),
                ),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="clinical_documents",
                        to="patients.patient",
                    ),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="clinical_documents_uploaded",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="anamnesisversion",
            constraint=models.UniqueConstraint(
                fields=("anamnesis", "version"), name="unique_anamnesis_version"
            ),
        ),
        migrations.AddConstraint(
            model_name="evolutionversion",
            constraint=models.UniqueConstraint(
                fields=("evolution", "version"), name="unique_evolution_version"
            ),
        ),
        migrations.AddIndex(
            model_name="treatmentgoal",
            index=models.Index(
                fields=["patient", "status"], name="goal_patient_status_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="clinicaldocument",
            index=models.Index(
                fields=["patient", "is_archived"], name="document_patient_archive_idx"
            ),
        ),
    ]
