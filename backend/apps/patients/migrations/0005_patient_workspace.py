import apps.patients.models
import core.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("patients", "0004_sync_patient_field_metadata"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="patient",
            name="cpf",
            field=models.CharField(blank=True, max_length=11, null=True, unique=True, validators=[core.validators.validate_cpf], verbose_name="CPF"),
        ),
        migrations.AlterField(
            model_name="patient",
            name="birth_date",
            field=models.DateField(blank=True, null=True, verbose_name="Data de nascimento"),
        ),
        migrations.AddField(model_name="patient", name="photo", field=models.FileField(blank=True, null=True, upload_to=apps.patients.models.patient_photo_path, verbose_name="Foto do paciente")),
        migrations.AddField(model_name="patient", name="treatment_start_date", field=models.DateField(blank=True, null=True, verbose_name="Início dos atendimentos")),
        migrations.AddField(model_name="patient", name="profession", field=models.CharField(blank=True, max_length=160, verbose_name="Profissão")),
        migrations.AddField(model_name="patient", name="social_network", field=models.CharField(blank=True, max_length=160, verbose_name="Rede social")),
        migrations.AddField(model_name="patient", name="reminders_enabled", field=models.BooleanField(default=True, verbose_name="Lembretes ativos")),
        migrations.AddField(model_name="patient", name="reminder_recipient", field=models.CharField(choices=[("patient", "Paciente"), ("financial_responsible", "Responsável financeiro"), ("both", "Paciente e responsável"), ("none", "Não enviar")], default="patient", max_length=32, verbose_name="Destinatário dos lembretes")),
        migrations.AddField(model_name="patient", name="financial_responsible_name", field=models.CharField(blank=True, max_length=255, verbose_name="Responsável financeiro")),
        migrations.AddField(model_name="patient", name="financial_responsible_cpf", field=models.CharField(blank=True, max_length=11, validators=[core.validators.validate_cpf], verbose_name="CPF do responsável financeiro")),
        migrations.AddField(model_name="patient", name="financial_responsible_phone", field=models.CharField(blank=True, max_length=20, validators=[core.validators.validate_phone], verbose_name="Telefone do responsável financeiro")),
        migrations.AddField(model_name="patient", name="financial_responsible_email", field=models.EmailField(blank=True, max_length=254, verbose_name="E-mail do responsável financeiro")),
        migrations.AddField(model_name="patient", name="financial_responsible_marital_status", field=models.CharField(blank=True, choices=[("single", "Solteiro(a)"), ("married", "Casado(a)"), ("divorced", "Divorciado(a)"), ("widowed", "Viúvo(a)"), ("other", "Outro")], max_length=16, verbose_name="Estado civil do responsável financeiro")),
        migrations.AddField(model_name="patient", name="financial_responsible_naturality", field=models.CharField(blank=True, max_length=120, verbose_name="Naturalidade do responsável financeiro")),
        migrations.AddField(model_name="patient", name="financial_responsible_occupation", field=models.CharField(blank=True, max_length=160, verbose_name="Ocupação do responsável financeiro")),
        migrations.AddField(model_name="patient", name="financial_responsible_relationship", field=models.CharField(blank=True, max_length=80, verbose_name="Relação do responsável financeiro")),
        migrations.AddIndex(model_name="patient", index=models.Index(fields=["birth_date"], name="patient_birth_date_idx")),
        migrations.AddIndex(model_name="patient", index=models.Index(fields=["payer_type", "insurance_name"], name="patient_payer_insurance_idx")),
        migrations.CreateModel(
            name="PatientProfessional",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_primary", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                ("assigned_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="patient_professionals_assigned", to=settings.AUTH_USER_MODEL)),
                ("patient", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="professional_links", to="patients.patient")),
                ("professional", models.ForeignKey(limit_choices_to={"role": "therapist"}, on_delete=django.db.models.deletion.PROTECT, related_name="patient_professional_links", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-is_primary", "professional__full_name"]},
        ),
        migrations.AddConstraint(model_name="patientprofessional", constraint=models.UniqueConstraint(fields=("patient", "professional"), name="unique_patient_professional")),
        migrations.AddIndex(model_name="patientprofessional", index=models.Index(fields=["professional", "is_active"], name="pat_prof_active_idx")),
    ]
