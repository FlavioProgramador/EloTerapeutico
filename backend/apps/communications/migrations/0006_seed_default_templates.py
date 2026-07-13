from django.db import migrations


TEMPLATES = [
    {"name": "Consulta criada", "slug": "appointment-created", "category": "appointment_confirmation", "subject_template": "Sua consulta foi agendada", "body_template": "Olá, {{patient_name}}.\n\nSua consulta com {{therapist_name}} foi agendada para {{appointment_date}}, às {{appointment_time}}.\n\nLocal/modalidade: {{appointment_location}}\n\nVocê pode confirmar sua presença pelo link:\n{{confirmation_link}}", "allowed_variables": ["patient_name", "therapist_name", "appointment_date", "appointment_time", "appointment_location", "confirmation_link"]},
    {"name": "Lembrete de consulta — 24 horas", "slug": "appointment-reminder-24h", "category": "appointment_reminder", "subject_template": "Lembrete da sua consulta", "body_template": "Olá, {{patient_name}}.\n\nEste é um lembrete da sua consulta com {{therapist_name}} amanhã, {{appointment_date}}, às {{appointment_time}}.\n\n{{confirmation_link}}", "allowed_variables": ["patient_name", "therapist_name", "appointment_date", "appointment_time", "confirmation_link"]},
    {"name": "Lembrete de consulta — 2 horas", "slug": "appointment-reminder-2h", "category": "appointment_reminder", "subject_template": "Sua consulta será em breve", "body_template": "Olá, {{patient_name}}.\n\nSua consulta está marcada para hoje, às {{appointment_time}}.\n\n{{meeting_link}}", "allowed_variables": ["patient_name", "appointment_time", "meeting_link"]},
    {"name": "Consulta reagendada", "slug": "appointment-rescheduled", "category": "appointment_rescheduled", "subject_template": "Sua consulta foi reagendada", "body_template": "Olá, {{patient_name}}.\n\nSua consulta foi reagendada para {{appointment_date}}, às {{appointment_time}}.", "allowed_variables": ["patient_name", "appointment_date", "appointment_time"]},
    {"name": "Consulta cancelada", "slug": "appointment-canceled", "category": "appointment_canceled", "subject_template": "Sua consulta foi cancelada", "body_template": "Olá, {{patient_name}}.\n\nA consulta marcada para {{appointment_date}}, às {{appointment_time}}, foi cancelada.", "allowed_variables": ["patient_name", "appointment_date", "appointment_time"]},
    {"name": "Formulário enviado", "slug": "form-request", "category": "form_request", "subject_template": "Formulário disponível para preenchimento", "body_template": "Olá, {{patient_name}}.\n\n{{therapist_name}} disponibilizou o formulário “{{form_name}}” para preenchimento.\n\nAcesse pelo link:\n{{form_link}}", "allowed_variables": ["patient_name", "therapist_name", "form_name", "form_link"]},
    {"name": "Lembrete de formulário", "slug": "form-reminder", "category": "form_reminder", "subject_template": "Lembrete de formulário pendente", "body_template": "Olá, {{patient_name}}.\n\nO formulário “{{form_name}}” ainda está aguardando preenchimento.\n\n{{form_link}}", "allowed_variables": ["patient_name", "form_name", "form_link"]},
    {"name": "Documento disponível", "slug": "document-available", "category": "document_available", "subject_template": "Documento disponível", "body_template": "Olá, {{patient_name}}.\n\nO documento “{{document_name}}” está disponível para acesso seguro.\n\n{{document_link}}", "allowed_variables": ["patient_name", "document_name", "document_link"]},
    {"name": "Solicitação de assinatura de documento", "slug": "document-signature-request", "category": "document_signature", "subject_template": "Documento aguardando assinatura", "body_template": "Olá, {{patient_name}}.\n\nO documento “{{document_name}}” está aguardando sua assinatura. Acesse pelo link seguro:\n\n{{document_link}}", "allowed_variables": ["patient_name", "document_name", "document_link"]},
    {"name": "Pagamento próximo do vencimento", "slug": "payment-due", "category": "payment_due", "subject_template": "Lembrete de pagamento", "body_template": "Olá, {{patient_name}}.\n\nHá um pagamento no valor de {{payment_amount}} com vencimento em {{payment_due_date}}.", "allowed_variables": ["patient_name", "payment_amount", "payment_due_date"]},
    {"name": "Pagamento vencido", "slug": "payment-overdue", "category": "payment_overdue", "subject_template": "Pagamento vencido", "body_template": "Olá, {{patient_name}}.\n\nConsta um pagamento administrativo no valor de {{payment_amount}} com vencimento em {{payment_due_date}}. Caso já tenha realizado o pagamento, desconsidere esta mensagem.", "allowed_variables": ["patient_name", "payment_amount", "payment_due_date"]},
    {"name": "Pagamento confirmado", "slug": "payment-confirmed", "category": "payment_confirmed", "subject_template": "Pagamento confirmado", "body_template": "Olá, {{patient_name}}.\n\nO pagamento no valor de {{payment_amount}} foi confirmado.", "allowed_variables": ["patient_name", "payment_amount"]},
    {"name": "Pacote próximo do fim", "slug": "package-ending", "category": "package_ending", "subject_template": "Seu pacote de sessões está próximo do fim", "body_template": "Olá, {{patient_name}}.\n\nSeu pacote possui {{package_remaining_sessions}} sessão(ões) restante(s). Entre em contato com {{therapist_name}} para orientações administrativas.", "allowed_variables": ["patient_name", "package_remaining_sessions", "therapist_name"]},
]

BLUEPRINTS = [
    ("Confirmação ao criar consulta", "appointment.created", "appointment-created", 0, "minutes", False),
    ("Lembrete 24 horas antes", "appointment.reminder_due", "appointment-reminder-24h", 24, "hours", True),
    ("Lembrete 2 horas antes", "appointment.reminder_due", "appointment-reminder-2h", 2, "hours", True),
    ("Aviso de reagendamento", "appointment.rescheduled", "appointment-rescheduled", 0, "minutes", False),
    ("Aviso de cancelamento", "appointment.canceled", "appointment-canceled", 0, "minutes", False),
    ("Envio de formulário", "form.assigned", "form-request", 0, "minutes", False),
    ("Lembrete de formulário pendente", "form.due_soon", "form-reminder", 0, "minutes", False),
    ("Documento disponível", "document.available", "document-available", 0, "minutes", False),
    ("Lembrete de assinatura", "document.signature_requested", "document-signature-request", 0, "minutes", False),
    ("Pagamento próximo do vencimento", "financial.payment_due_soon", "payment-due", 0, "minutes", False),
    ("Pagamento vencido", "financial.payment_overdue", "payment-overdue", 0, "minutes", False),
    ("Pagamento confirmado", "financial.payment_confirmed", "payment-confirmed", 0, "minutes", False),
    ("Pacote próximo do fim", "financial.package_ending", "package-ending", 0, "minutes", False),
]


def seed_templates(apps, schema_editor):
    Template = apps.get_model("communications", "CommunicationTemplate")
    Automation = apps.get_model("communications", "CommunicationAutomation")
    Channel = apps.get_model("communications", "CommunicationChannelConfig")
    User = apps.get_model("users", "User")
    for item in TEMPLATES:
        Template.objects.update_or_create(
            owner=None,
            slug=item["slug"],
            channel="email",
            defaults={**item, "description": "Template operacional padrão do Elo Terapêutico.", "is_system_template": True, "is_active": True, "is_archived": False},
        )
    for user in User.objects.all().iterator():
        for channel, active, connection, provider in [
            ("in_app", True, "configured", "in_app"),
            ("email", True, "configured", "django_email"),
            ("whatsapp_manual", True, "configured", "whatsapp_manual"),
            ("whatsapp", False, "not_configured", ""),
            ("sms", False, "not_configured", ""),
        ]:
            Channel.objects.get_or_create(owner=user, channel=channel, defaults={"is_active": active, "connection_status": connection, "provider": provider})
        for name, event_type, slug, delay, unit, before in BLUEPRINTS:
            template = Template.objects.get(owner=None, slug=slug, channel="email")
            Automation.objects.get_or_create(
                owner=user,
                name=name,
                defaults={"description": "Automação sugerida pelo Elo Terapêutico. Revise antes de ativar.", "event_type": event_type, "channel": "email", "template": template, "is_active": False, "delay_value": delay, "delay_unit": unit, "send_before_event": before, "respect_preferences": True, "created_by": user, "updated_by": user},
            )


def unseed_templates(apps, schema_editor):
    Template = apps.get_model("communications", "CommunicationTemplate")
    Template.objects.filter(owner=None, is_system_template=True, slug__in=[item["slug"] for item in TEMPLATES]).delete()


class Migration(migrations.Migration):
    dependencies = [("communications", "0005_constraints_indexes")]
    operations = [migrations.RunPython(seed_templates, unseed_templates)]
