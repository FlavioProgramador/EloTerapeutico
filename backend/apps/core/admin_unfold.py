"""Configuração visual do Django Unfold para o backoffice interno."""

from django.urls import reverse_lazy


def _admin_link(route_name: str):
    return reverse_lazy(route_name)


UNFOLD = {
    "COLORS": {
        "primary": {
            "50": "254 243 199",
            "100": "253 230 138",
            "200": "252 211 77",
            "300": "251 191 36",
            "400": "245 158 11",
            "500": "217 142 63",  # #D98E3F (Brand Amber)
            "600": "180 83 9",
            "700": "146 64 14",
            "800": "120 53 4",
            "900": "78 35 9",
            "950": "45 20 4",
        },
    },
    "SITE_TITLE": "Elo Terapêutico Admin",
    "SITE_HEADER": "Elo Terapêutico",
    "SITE_SUBHEADER": "Painel interno da plataforma",
    "SITE_SYMBOL": "psychology",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "DASHBOARD_CALLBACK": "apps.core.admin_dashboard.dashboard_callback",
    "ENVIRONMENT": "apps.core.admin_dashboard.environment_callback",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Visão Geral",
                "separator": True,
                "items": [
                    {
                        "title": "Dashboard",
                        "icon": "dashboard",
                        "link": _admin_link("admin:index"),
                    },
                    {
                        "title": "SQL Explorer",
                        "icon": "database",
                        "link": _admin_link("sql_explorer"),
                    },
                ],
            },
            {
                "title": "Usuários e Acessos",
                "separator": True,
                "items": [
                    {
                        "title": "Usuários",
                        "icon": "manage_accounts",
                        "link": _admin_link("admin:users_user_changelist"),
                    },
                    {
                        "title": "Grupos",
                        "icon": "groups",
                        "link": _admin_link("admin:auth_group_changelist"),
                    },
                    {
                        "title": "Horários de atendimento",
                        "icon": "schedule",
                        "link": _admin_link("admin:users_workinghours_changelist"),
                    },
                ],
            },
            {
                "title": "Pacientes",
                "separator": True,
                "items": [
                    {
                        "title": "Pacientes",
                        "icon": "personal_injury",
                        "link": _admin_link("admin:patients_patient_changelist"),
                    },
                ],
            },
            {
                "title": "Agenda",
                "separator": True,
                "items": [
                    {
                        "title": "Agendamentos",
                        "icon": "event",
                        "link": _admin_link("admin:agenda_appointment_changelist"),
                    },
                    {
                        "title": "Recorrências",
                        "icon": "event_repeat",
                        "link": _admin_link("admin:agenda_appointmentrecurrence_changelist"),
                    },
                    {
                        "title": "Bloqueios de agenda",
                        "icon": "event_busy",
                        "link": _admin_link("admin:agenda_scheduleblock_changelist"),
                    },
                    {
                        "title": "Salas",
                        "icon": "meeting_room",
                        "link": _admin_link("admin:agenda_room_changelist"),
                    },
                    {
                        "title": "Pacotes de sessões",
                        "icon": "inventory_2",
                        "link": _admin_link("admin:agenda_patientpackage_changelist"),
                    },
                    {
                        "title": "Sessões de pacote",
                        "icon": "checklist",
                        "link": _admin_link("admin:agenda_packagesession_changelist"),
                    },
                    {
                        "title": "Telemedicina",
                        "icon": "video_call",
                        "link": _admin_link("admin:agenda_telemedicineroom_changelist"),
                    },
                    {
                        "title": "Lembretes",
                        "icon": "notifications",
                        "link": _admin_link("admin:agenda_appointmentreminder_changelist"),
                    },
                ],
            },
            {
                "title": "Prontuários",
                "separator": True,
                "items": [
                    {
                        "title": "Anamneses",
                        "icon": "assignment",
                        "link": _admin_link("admin:records_anamnesis_changelist"),
                    },
                    {
                        "title": "Evoluções",
                        "icon": "clinical_notes",
                        "link": _admin_link("admin:records_evolution_changelist"),
                    },
                    {
                        "title": "Aditivos",
                        "icon": "post_add",
                        "link": _admin_link("admin:records_evolutionaddendum_changelist"),
                    },
                ],
            },
            {
                "title": "Financeiro",
                "separator": True,
                "items": [
                    {
                        "title": "Transações financeiras",
                        "icon": "payments",
                        "link": _admin_link("admin:financeiro_financialtransaction_changelist"),
                    },
                ],
            },
            {
                "title": "Documentos",
                "separator": True,
                "items": [
                    {
                        "title": "Templates",
                        "icon": "article",
                        "link": _admin_link("admin:documents_documenttemplate_changelist"),
                    },
                    {
                        "title": "Documentos gerados",
                        "icon": "description",
                        "link": _admin_link("admin:documents_generateddocument_changelist"),
                    },
                    {
                        "title": "Sequências",
                        "icon": "format_list_numbered",
                        "link": _admin_link("admin:documents_documentsequence_changelist"),
                    },
                ],
            },
            {
                "title": "Formulários",
                "separator": True,
                "items": [
                    {
                        "title": "Templates de formulário",
                        "icon": "dynamic_form",
                        "link": _admin_link("admin:forms_formtemplate_changelist"),
                    },
                    {
                        "title": "Formulários terapêuticos",
                        "icon": "fact_check",
                        "link": _admin_link("admin:forms_therapeuticform_changelist"),
                    },
                    {
                        "title": "Respostas enviadas",
                        "icon": "rate_review",
                        "link": _admin_link("admin:forms_formsubmission_changelist"),
                    },
                    {
                        "title": "Itens de resposta",
                        "icon": "subject",
                        "link": _admin_link("admin:forms_formanswer_changelist"),
                    },
                ],
            },
        ],
    },
}
