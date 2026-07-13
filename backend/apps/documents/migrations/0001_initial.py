# Generated for the documents module.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Q

import apps.core.fields
import apps.documents.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("patients", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentSequence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.PositiveSmallIntegerField()),
                ("last_value", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="document_sequences",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="DocumentTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("name", models.CharField(max_length=160)),
                ("description", models.CharField(blank=True, max_length=500)),
                ("category", models.CharField(db_index=True, max_length=100)),
                (
                    "document_type",
                    models.CharField(
                        choices=[
                            ("declaration", "Declaração"),
                            ("report", "Relatório"),
                            ("referral", "Encaminhamento"),
                            ("certificate", "Atestado"),
                            ("consent", "Termo de consentimento"),
                            ("other", "Outro"),
                        ],
                        db_index=True,
                        default="other",
                        max_length=32,
                    ),
                ),
                ("specialty", models.CharField(blank=True, db_index=True, max_length=120)),
                ("content", apps.core.fields.EncryptedTextField()),
                ("header_content", apps.core.fields.EncryptedTextField(blank=True, default="")),
                ("footer_content", apps.core.fields.EncryptedTextField(blank=True, default="")),
                ("include_professional_identification", models.BooleanField(default=True)),
                ("include_clinic_identification", models.BooleanField(default=True)),
                ("requires_signature", models.BooleanField(default=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Ativo"), ("inactive", "Inativo"), ("archived", "Arquivado")],
                        db_index=True,
                        default="active",
                        max_length=16,
                    ),
                ),
                ("is_library_template", models.BooleanField(db_index=True, default=False)),
                ("version", models.PositiveIntegerField(default=1)),
                ("usage_count", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("archived_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="document_templates_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        help_text="Nulo apenas para templates globais da biblioteca.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="document_templates",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "source_library_template",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="imported_copies",
                        to="documents.documenttemplate",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="document_templates_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "permissions": [("manage_document_library", "Can manage the global document template library")],
            },
        ),
        migrations.CreateModel(
            name="GeneratedDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ("title", models.CharField(max_length=200)),
                (
                    "document_type",
                    models.CharField(
                        choices=[
                            ("declaration", "Declaração"),
                            ("report", "Relatório"),
                            ("referral", "Encaminhamento"),
                            ("certificate", "Atestado"),
                            ("consent", "Termo de consentimento"),
                            ("other", "Outro"),
                        ],
                        db_index=True,
                        default="other",
                        max_length=32,
                    ),
                ),
                ("category", models.CharField(db_index=True, max_length=100)),
                ("document_number", models.CharField(max_length=32)),
                ("template_name_snapshot", models.CharField(max_length=160)),
                ("template_version_snapshot", models.PositiveIntegerField(default=1)),
                ("template_content_snapshot", apps.core.fields.EncryptedTextField()),
                ("template_header_snapshot", apps.core.fields.EncryptedTextField(blank=True, default="")),
                ("template_footer_snapshot", apps.core.fields.EncryptedTextField(blank=True, default="")),
                ("include_professional_identification_snapshot", models.BooleanField(default=True)),
                ("include_clinic_identification_snapshot", models.BooleanField(default=True)),
                ("requires_signature_snapshot", models.BooleanField(default=True)),
                ("rendered_content", apps.core.fields.EncryptedTextField()),
                ("context_snapshot", apps.core.fields.EncryptedTextField(default="{}")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Rascunho"),
                            ("processing", "Processando"),
                            ("completed", "Concluído"),
                            ("failed", "Falhou"),
                            ("cancelled", "Cancelado"),
                            ("archived", "Arquivado"),
                        ],
                        db_index=True,
                        default="draft",
                        max_length=16,
                    ),
                ),
                ("pdf_file", models.FileField(blank=True, null=True, upload_to=apps.documents.models.generated_document_path)),
                ("pdf_hash", models.CharField(blank=True, db_index=True, max_length=64)),
                ("signature_hash", models.CharField(blank=True, max_length=64)),
                ("professional_name_snapshot", models.CharField(max_length=255)),
                ("professional_registration_snapshot", models.CharField(blank=True, max_length=50)),
                ("failure_reason", models.CharField(blank=True, max_length=500)),
                ("idempotency_key", models.CharField(blank=True, max_length=128, null=True)),
                ("generated_at", models.DateTimeField(blank=True, null=True)),
                ("signed_at", models.DateTimeField(blank=True, null=True)),
                ("archived_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "owner",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="generated_documents", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "patient",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="generated_documents", to="patients.patient"),
                ),
                (
                    "professional",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="documents_issued", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "template",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="generated_documents", to="documents.documenttemplate"),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(model_name="documenttemplate", index=models.Index(fields=["owner", "status"], name="doc_tpl_owner_status_idx")),
        migrations.AddIndex(model_name="documenttemplate", index=models.Index(fields=["is_library_template", "specialty"], name="doc_tpl_library_spec_idx")),
        migrations.AddIndex(model_name="documenttemplate", index=models.Index(fields=["document_type", "category"], name="doc_tpl_type_cat_idx")),
        migrations.AddConstraint(
            model_name="documenttemplate",
            constraint=models.UniqueConstraint(condition=Q(("archived_at__isnull", True), ("owner__isnull", False)), fields=("owner", "name"), name="unique_active_document_template_owner_name"),
        ),
        migrations.AddConstraint(
            model_name="documenttemplate",
            constraint=models.UniqueConstraint(condition=Q(("archived_at__isnull", True), ("is_library_template", True), ("owner__isnull", True)), fields=("name",), name="unique_active_library_template_name"),
        ),
        migrations.AddConstraint(
            model_name="documenttemplate",
            constraint=models.CheckConstraint(condition=Q(Q(("is_library_template", False), ("owner__isnull", False)), Q(("is_library_template", True), ("owner__isnull", True)), _connector="OR"), name="document_template_scope_consistent"),
        ),
        migrations.AddConstraint(
            model_name="documentsequence",
            constraint=models.UniqueConstraint(fields=("owner", "year"), name="unique_document_sequence_owner_year"),
        ),
        migrations.AddIndex(model_name="generateddocument", index=models.Index(fields=["owner", "status"], name="gen_doc_owner_status_idx")),
        migrations.AddIndex(model_name="generateddocument", index=models.Index(fields=["patient", "created_at"], name="gen_doc_patient_date_idx")),
        migrations.AddIndex(model_name="generateddocument", index=models.Index(fields=["document_type", "created_at"], name="gen_doc_type_date_idx")),
        migrations.AddConstraint(
            model_name="generateddocument",
            constraint=models.UniqueConstraint(fields=("owner", "document_number"), name="unique_generated_document_number_owner"),
        ),
        migrations.AddConstraint(
            model_name="generateddocument",
            constraint=models.UniqueConstraint(condition=Q(("idempotency_key__isnull", False)), fields=("owner", "idempotency_key"), name="unique_generated_document_idempotency_owner"),
        ),
    ]
