from django.db import migrations, models
import core.validators


class Migration(migrations.Migration):
    dependencies = [("patients", "0002_initial")]

    operations = [
        migrations.AddField(
            model_name="patient",
            name="social_name",
            field=models.CharField(blank=True, max_length=255, verbose_name="Nome social"),
        ),
        migrations.AddField(
            model_name="patient",
            name="rg",
            field=models.CharField(blank=True, max_length=30, verbose_name="RG"),
        ),
        migrations.AddField(
            model_name="patient",
            name="marital_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("single", "Solteiro(a)"),
                    ("married", "Casado(a)"),
                    ("divorced", "Divorciado(a)"),
                    ("widowed", "Viúvo(a)"),
                    ("other", "Outro"),
                ],
                max_length=16,
                verbose_name="Estado civil",
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="whatsapp",
            field=models.CharField(
                blank=True,
                max_length=20,
                validators=[core.validators.validate_phone],
                verbose_name="WhatsApp",
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="attendance_type",
            field=models.CharField(
                choices=[
                    ("individual", "Individual"),
                    ("couple", "Casal"),
                    ("family", "Familiar"),
                    ("group", "Grupo"),
                    ("other", "Outro"),
                ],
                default="individual",
                max_length=20,
                verbose_name="Tipo de atendimento",
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="modality",
            field=models.CharField(
                choices=[
                    ("in_person", "Presencial"),
                    ("online", "Online"),
                    ("hybrid", "Híbrido"),
                ],
                default="in_person",
                max_length=20,
                verbose_name="Modalidade",
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="payer_type",
            field=models.CharField(
                choices=[("private", "Particular"), ("insurance", "Convênio")],
                default="private",
                max_length=20,
                verbose_name="Forma de atendimento",
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="insurance_name",
            field=models.CharField(blank=True, max_length=120, verbose_name="Convênio"),
        ),
        migrations.AddField(
            model_name="patient",
            name="session_value",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=8,
                verbose_name="Valor de referência da sessão",
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="planned_frequency",
            field=models.CharField(
                blank=True,
                choices=[
                    ("weekly", "Semanal"),
                    ("biweekly", "Quinzenal"),
                    ("monthly", "Mensal"),
                    ("as_needed", "Conforme necessidade"),
                ],
                max_length=20,
                verbose_name="Frequência planejada",
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="tags",
            field=models.JSONField(blank=True, default=list, verbose_name="Etiquetas"),
        ),
        migrations.AddField(
            model_name="patient",
            name="emergency_contact_name",
            field=models.CharField(blank=True, max_length=255, verbose_name="Contato de emergência"),
        ),
        migrations.AddField(
            model_name="patient",
            name="emergency_contact_relationship",
            field=models.CharField(blank=True, max_length=80, verbose_name="Parentesco do contato"),
        ),
        migrations.AddField(
            model_name="patient",
            name="emergency_contact_phone",
            field=models.CharField(
                blank=True,
                max_length=20,
                validators=[core.validators.validate_phone],
                verbose_name="Telefone de emergência",
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="guardian_phone",
            field=models.CharField(
                blank=True,
                max_length=20,
                validators=[core.validators.validate_phone],
                verbose_name="Telefone do responsável",
            ),
        ),
        migrations.AddField(
            model_name="patient",
            name="guardian_email",
            field=models.EmailField(blank=True, max_length=254, verbose_name="E-mail do responsável"),
        ),
        migrations.AddField(
            model_name="patient",
            name="guardian_relationship",
            field=models.CharField(blank=True, max_length=80, verbose_name="Parentesco do responsável"),
        ),
        migrations.AddField(
            model_name="patient",
            name="consent_terms_accepted",
            field=models.BooleanField(default=False, verbose_name="Consentimentos registrados"),
        ),
        migrations.AddField(
            model_name="patient",
            name="consent_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Consentimento registrado em"),
        ),
        migrations.AlterField(
            model_name="patient",
            name="status",
            field=models.CharField(
                choices=[
                    ("active", "Ativo"),
                    ("evaluation", "Em avaliação"),
                    ("waiting_return", "Aguardando retorno"),
                    ("discharged", "Alta"),
                    ("inactive", "Encerrado"),
                    ("archived", "Arquivado"),
                ],
                db_index=True,
                default="active",
                max_length=20,
                verbose_name="Status",
            ),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(fields=["therapist", "status"], name="patient_owner_status_idx"),
        ),
        migrations.AddIndex(
            model_name="patient",
            index=models.Index(fields=["created_at"], name="patient_created_at_idx"),
        ),
    ]
