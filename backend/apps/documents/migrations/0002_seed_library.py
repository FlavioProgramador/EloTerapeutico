from django.db import migrations


LIBRARY_TEMPLATES = [
    {
        "name": "Declaração de Acompanhamento Psicológico",
        "description": "Declara que o paciente realiza acompanhamento profissional.",
        "category": "Declaração",
        "document_type": "declaration",
        "specialty": "Psicologia",
        "content": "# Declaração de acompanhamento\n\nDeclaro, para os devidos fins, que **{{paciente.nome_completo}}** realiza acompanhamento psicológico sob minha responsabilidade profissional.\n\nDocumento emitido em {{documento.data_emissao}}, sob o número {{documento.numero}}.",
    },
    {
        "name": "Declaração de Atendimento Fonoaudiológico",
        "description": "Comprova atendimento ou acompanhamento fonoaudiológico.",
        "category": "Declaração",
        "document_type": "declaration",
        "specialty": "Fonoaudiologia",
        "content": "# Declaração de atendimento\n\nDeclaro que **{{paciente.nome_completo}}** encontra-se em atendimento fonoaudiológico com {{profissional.nome}}, {{profissional.registro_profissional}}.\n\n{{documento.local_emissao}}, {{documento.data_emissao}}.",
    },
    {
        "name": "Declaração de Comparecimento",
        "description": "Registra o comparecimento do paciente ao atendimento.",
        "category": "Declaração",
        "document_type": "declaration",
        "specialty": "Psicologia",
        "content": "# Declaração de comparecimento\n\nDeclaro que **{{paciente.nome}}** compareceu a atendimento profissional nesta data.\n\nEmitido em {{documento.data_emissao}}.",
    },
    {
        "name": "Declaração para Escola",
        "description": "Modelo editável de comunicação de acompanhamento à instituição de ensino.",
        "category": "Declaração",
        "document_type": "declaration",
        "specialty": "Psicologia",
        "content": "# Declaração\n\nDeclaro, mediante autorização do responsável, que **{{paciente.nome_completo}}** realiza acompanhamento profissional. Este documento limita-se à confirmação do acompanhamento e não contém informações clínicas adicionais.\n\n{{documento.data_emissao}}.",
    },
    {
        "name": "Encaminhamento para Avaliação Médica",
        "description": "Estrutura inicial para encaminhamento a avaliação médica.",
        "category": "Encaminhamento",
        "document_type": "referral",
        "specialty": "Fonoaudiologia",
        "content": "# Encaminhamento\n\nEncaminho **{{paciente.nome_completo}}** para avaliação médica.\n\n## Motivo do encaminhamento\n\n[Descreva de forma objetiva o motivo e as informações pertinentes.]\n\n{{profissional.nome}} — {{profissional.registro_profissional}}",
    },
    {
        "name": "Encaminhamento Multidisciplinar",
        "description": "Estrutura para encaminhamento a outro profissional da rede de cuidado.",
        "category": "Encaminhamento",
        "document_type": "referral",
        "specialty": "Terapia Ocupacional",
        "content": "# Encaminhamento multidisciplinar\n\nPaciente: **{{paciente.nome_completo}}**\n\n## Objetivo\n\n[Informe o objetivo do encaminhamento.]\n\n## Informações relevantes\n\n[Inclua somente as informações necessárias e autorizadas.]",
    },
    {
        "name": "Encaminhamento para Psiquiatria",
        "description": "Modelo editável para solicitação de avaliação psiquiátrica.",
        "category": "Encaminhamento",
        "document_type": "referral",
        "specialty": "Psicologia",
        "content": "# Encaminhamento para avaliação psiquiátrica\n\nEncaminho **{{paciente.nome_completo}}** para avaliação psiquiátrica.\n\n## Contexto e objetivo\n\n[Descreva objetivamente o contexto clínico necessário e o objetivo do encaminhamento.]",
    },
    {
        "name": "Relatório de Acompanhamento",
        "description": "Estrutura de relatório profissional para personalização.",
        "category": "Relatório",
        "document_type": "report",
        "specialty": "",
        "content": "# Relatório de acompanhamento\n\n## Identificação\n\nPaciente: **{{paciente.nome_completo}}**\nProfissional: {{profissional.nome}} — {{profissional.registro_profissional}}\n\n## Finalidade\n\n[Informe a finalidade do documento.]\n\n## Procedimentos e período\n\n[Descreva somente as informações pertinentes.]\n\n## Considerações\n\n[Apresente as considerações profissionais revisadas.]",
    },
]


def seed_library(apps, schema_editor):
    DocumentTemplate = apps.get_model("documents", "DocumentTemplate")
    for payload in LIBRARY_TEMPLATES:
        DocumentTemplate.objects.update_or_create(
            owner=None,
            name=payload["name"],
            defaults={
                **payload,
                "is_library_template": True,
                "status": "active",
                "requires_signature": True,
                "include_professional_identification": True,
                "include_clinic_identification": True,
            },
        )


def remove_seeded_library(apps, schema_editor):
    DocumentTemplate = apps.get_model("documents", "DocumentTemplate")
    DocumentTemplate.objects.filter(
        owner=None,
        name__in=[item["name"] for item in LIBRARY_TEMPLATES],
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("documents", "0001_initial")]

    operations = [migrations.RunPython(seed_library, remove_seeded_library)]
