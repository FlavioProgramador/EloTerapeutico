from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


TEMPLATE_FIELDS = {
    "Anamnese Adulto": [
        "Queixa principal", "Histórico do problema atual", "Histórico de saúde", "Uso de medicamentos", "Histórico familiar", "Rotina e hábitos", "Sono", "Alimentação", "Objetivos terapêuticos",
    ],
    "Anamnese Infantil": [
        "Responsável pelo preenchimento", "Queixa principal", "Desenvolvimento da criança", "Rotina familiar", "Escola e aprendizagem", "Sono", "Alimentação", "Comportamentos observados", "Objetivos do acompanhamento",
    ],
    "Avaliação Psicológica": [
        "Motivo da avaliação", "Instrumentos utilizados", "Observações comportamentais", "Histórico relevante", "Resultados obtidos", "Análise clínica", "Hipóteses", "Recomendações", "Conclusão",
    ],
    "Relato de Sessão": [
        "Data da sessão", "Objetivo da sessão", "Temas abordados", "Intervenções realizadas", "Resposta do paciente", "Orientações/tarefas", "Observações para próxima sessão",
    ],
}

SYSTEM_TEMPLATES = [
    ("Anamnese Adulto", "Formulário completo de anamnese para pacientes adultos", "anamnese", "clipboard"),
    ("Anamnese Infantil", "Formulário de anamnese adaptado para crianças", "anamnese", "smile"),
    ("Avaliação Psicológica", "Estrutura para relatório de avaliação psicológica", "avaliacao", "brain"),
    ("Relato de Sessão", "Registro estruturado de sessões de atendimento", "evolucao", "file-text"),
    ("Escala de Ansiedade (GAD-7)", "Questionário de triagem para acompanhamento de sintomas de ansiedade", "escalas", "bar-chart"),
]

GAD_FIELDS = [f"Item {index}" for index in range(1, 8)] + ["Impacto na rotina"]


def build_fields(name):
    labels = TEMPLATE_FIELDS.get(name, GAD_FIELDS)
    fields = []
    for index, label in enumerate(labels, start=1):
        field_type = "date" if label == "Data da sessão" else "scale" if name.startswith("Escala") and index <= 7 else "short_text" if label in {"Sono", "Alimentação", "Responsável pelo preenchimento", "Impacto na rotina"} else "long_text"
        config = {"rows": 4, "max_length": 2000} if field_type == "long_text" else {"max_length": 255}
        if field_type == "scale":
            config = {"min": 0, "max": 3, "step": 1, "min_label": "Nunca", "max_label": "Quase todos os dias"}
        if field_type == "date":
            config = {"allow_past": True, "allow_future": False}
        fields.append({"type": field_type, "label": label, "required": index == 1, "order": index, "config": config})
    return fields


def seed_templates(apps, schema_editor):
    FormTemplate = apps.get_model("forms", "FormTemplate")
    for name, description, category, icon in SYSTEM_TEMPLATES:
        FormTemplate.objects.update_or_create(
            name=name,
            defaults={
                "description": description,
                "category": category,
                "icon": icon,
                "fields_schema": build_fields(name),
                "is_system_template": True,
                "is_active": True,
            },
        )


def remove_templates(apps, schema_editor):
    apps.get_model("forms", "FormTemplate").objects.filter(is_system_template=True).delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("patients", "0001_initial"),
        ("agenda", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FormTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=180)),
                ("description", models.TextField(blank=True)),
                ("category", models.CharField(choices=[("anamnese", "Anamnese"), ("avaliacao", "Avaliação"), ("evolucao", "Evolução"), ("escalas", "Escalas"), ("questionario", "Questionário"), ("outro", "Outro")], db_index=True, max_length=32)),
                ("icon", models.CharField(blank=True, max_length=64)),
                ("fields_schema", models.JSONField(blank=True, default=list)),
                ("is_system_template", models.BooleanField(db_index=True, default=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["category", "name"]},
        ),
        migrations.CreateModel(
            name="TherapeuticForm",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(db_index=True, max_length=180)),
                ("description", models.TextField(blank=True)),
                ("category", models.CharField(choices=[("anamnese", "Anamnese"), ("avaliacao", "Avaliação"), ("evolucao", "Evolução"), ("escalas", "Escalas"), ("questionario", "Questionário"), ("outro", "Outro")], db_index=True, default="outro", max_length=32)),
                ("status", models.CharField(choices=[("active", "Ativo"), ("archived", "Arquivado")], db_index=True, default="active", max_length=16)),
                ("archived_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="forms_authored", to=settings.AUTH_USER_MODEL)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="forms_created", to=settings.AUTH_USER_MODEL)),
                ("source_template", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="forms", to="forms.formtemplate")),
                ("updated_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="forms_updated", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="FormField",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(choices=[("short_text", "Texto curto"), ("long_text", "Texto longo"), ("number", "Número"), ("date", "Data"), ("select", "Seleção"), ("radio", "Múltipla escolha"), ("checkbox", "Caixas de seleção"), ("scale", "Escala"), ("heading", "Título")], max_length=24)),
                ("label", models.CharField(max_length=180)),
                ("placeholder", models.CharField(blank=True, max_length=255)),
                ("help_text", models.CharField(blank=True, max_length=255)),
                ("required", models.BooleanField(default=False)),
                ("order", models.PositiveIntegerField(default=1)),
                ("is_visible", models.BooleanField(default=True)),
                ("internal_id", models.SlugField(blank=True, max_length=80)),
                ("config", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("form", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="fields", to="forms.therapeuticform")),
            ],
            options={"ordering": ["order", "id"]},
        ),
        migrations.CreateModel(
            name="FormSubmission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("draft", "Rascunho"), ("submitted", "Enviado"), ("reviewed", "Revisado"), ("archived", "Arquivado")], db_index=True, default="draft", max_length=16)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("appointment", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="form_submissions", to="agenda.appointment")),
                ("form", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="submissions", to="forms.therapeuticform")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="form_submissions", to=settings.AUTH_USER_MODEL)),
                ("patient", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="form_submissions", to="patients.patient")),
                ("professional", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="form_submissions_as_professional", to=settings.AUTH_USER_MODEL)),
                ("submitted_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="form_submissions_sent", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="FormAnswer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("value", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("field", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="answers", to="forms.formfield")),
                ("submission", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="answers", to="forms.formsubmission")),
            ],
            options={"ordering": ["field__order", "id"]},
        ),
        migrations.AddIndex(model_name="formtemplate", index=models.Index(fields=["category", "is_active"], name="form_tpl_cat_active_idx")),
        migrations.AddIndex(model_name="therapeuticform", index=models.Index(fields=["owner", "status"], name="form_owner_status_idx")),
        migrations.AddIndex(model_name="therapeuticform", index=models.Index(fields=["owner", "category"], name="form_owner_category_idx")),
        migrations.AddIndex(model_name="formfield", index=models.Index(fields=["form", "order"], name="form_field_order_idx")),
        migrations.AddIndex(model_name="formsubmission", index=models.Index(fields=["owner", "status"], name="submission_owner_status_idx")),
        migrations.AddConstraint(model_name="formanswer", constraint=models.UniqueConstraint(fields=("submission", "field"), name="unique_form_answer_field")),
        migrations.RunPython(seed_templates, remove_templates),
    ]
