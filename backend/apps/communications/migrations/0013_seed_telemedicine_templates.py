from django.db import migrations


TEMPLATES = [
    {
        "name": "Consulta online agendada",
        "slug": "telemedicine-invitation",
        "category": "appointment_confirmation",
        "subject_template": "Acesso ao seu atendimento online",
        "body_template": (
            "Olá, {{patient_name}}.\n\n"
            "Seu atendimento online com {{therapist_name}} está agendado para "
            "{{appointment_date}}, às {{appointment_time}}.\n\n"
            "Acesse pelo convite individual:\n{{meeting_link}}\n\n"
            "Use um ambiente reservado e fones quando possível. A chamada não é gravada."
        ),
    },
    {
        "name": "Lembrete de consulta online",
        "slug": "telemedicine-reminder",
        "category": "appointment_reminder",
        "subject_template": "Lembrete do seu atendimento online",
        "body_template": (
            "Olá, {{patient_name}}.\n\n"
            "Seu atendimento online com {{therapist_name}} será em "
            "{{appointment_date}}, às {{appointment_time}}.\n\n"
            "Convite individual:\n{{meeting_link}}"
        ),
    },
    {
        "name": "Consulta online reagendada",
        "slug": "telemedicine-rescheduled",
        "category": "appointment_rescheduled",
        "subject_template": "Seu atendimento online foi reagendado",
        "body_template": (
            "Olá, {{patient_name}}.\n\n"
            "Seu atendimento online foi reagendado para {{appointment_date}}, "
            "às {{appointment_time}}.\n\n"
            "Use este novo convite:\n{{meeting_link}}"
        ),
    },
    {
        "name": "Convite online substituído",
        "slug": "telemedicine-link-regenerated",
        "category": "appointment_confirmation",
        "subject_template": "Novo acesso ao atendimento online",
        "body_template": (
            "Olá, {{patient_name}}.\n\n"
            "O convite anterior foi substituído. Use somente este novo acesso "
            "para o atendimento com {{therapist_name}}:\n\n{{meeting_link}}"
        ),
    },
    {
        "name": "Consulta online cancelada",
        "slug": "telemedicine-canceled",
        "category": "appointment_canceled",
        "subject_template": "Atendimento online cancelado",
        "body_template": (
            "Olá, {{patient_name}}.\n\n"
            "O atendimento online marcado para {{appointment_date}}, às "
            "{{appointment_time}}, foi cancelado. O convite anterior não permite mais acesso."
        ),
    },
]

CHANNELS = ("email", "whatsapp_manual")
ALLOWED_VARIABLES = [
    "patient_name",
    "therapist_name",
    "appointment_date",
    "appointment_time",
    "meeting_link",
]


def seed_templates(apps, schema_editor):
    Template = apps.get_model("communications", "CommunicationTemplate")
    for channel in CHANNELS:
        for item in TEMPLATES:
            Template.objects.update_or_create(
                organization=None,
                owner=None,
                slug=item["slug"],
                channel=channel,
                defaults={
                    **item,
                    "description": (
                        "Template operacional de telemedicina. Não inclua conteúdo clínico."
                    ),
                    "allowed_variables": ALLOWED_VARIABLES,
                    "is_system_template": True,
                    "is_active": True,
                    "is_archived": False,
                },
            )


def unseed_templates(apps, schema_editor):
    Template = apps.get_model("communications", "CommunicationTemplate")
    Template.objects.filter(
        organization__isnull=True,
        owner__isnull=True,
        is_system_template=True,
        slug__in=[item["slug"] for item in TEMPLATES],
        channel__in=CHANNELS,
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("communications", "0012_organization_tenant")]

    operations = [migrations.RunPython(seed_templates, unseed_templates)]
