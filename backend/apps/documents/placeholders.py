"""Whitelist e renderização segura dos marcadores de documentos."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

PLACEHOLDER_PATTERN = re.compile(r"{{\s*([a-zA-Z0-9_.]+)\s*}}")
MAX_TEMPLATE_LENGTH = 50_000


@dataclass(frozen=True)
class PlaceholderDefinition:
    key: str
    label: str
    group: str
    description: str


PLACEHOLDER_DEFINITIONS = (
    PlaceholderDefinition("paciente.nome", "Nome do paciente", "Paciente", "Nome preferencial do paciente."),
    PlaceholderDefinition("paciente.nome_completo", "Nome completo", "Paciente", "Nome civil completo."),
    PlaceholderDefinition("paciente.nome_social", "Nome social", "Paciente", "Nome social, quando informado."),
    PlaceholderDefinition("paciente.cpf", "CPF", "Paciente", "CPF formatado do paciente."),
    PlaceholderDefinition("paciente.data_nascimento", "Data de nascimento", "Paciente", "Data no formato brasileiro."),
    PlaceholderDefinition("paciente.idade", "Idade", "Paciente", "Idade calculada na data de emissão."),
    PlaceholderDefinition("paciente.responsavel_nome", "Responsável legal", "Paciente", "Nome do responsável legal."),
    PlaceholderDefinition("profissional.nome", "Nome do profissional", "Profissional", "Nome completo do profissional emissor."),
    PlaceholderDefinition("profissional.registro_profissional", "Registro profissional", "Profissional", "Número de registro cadastrado."),
    PlaceholderDefinition("profissional.especialidade", "Especialidade", "Profissional", "Especialidade cadastrada."),
    PlaceholderDefinition("clinica.nome", "Nome da clínica", "Clínica", "Nome configurado para emissão de documentos."),
    PlaceholderDefinition("clinica.endereco", "Endereço da clínica", "Clínica", "Endereço configurado no ambiente."),
    PlaceholderDefinition("clinica.telefone", "Telefone da clínica", "Clínica", "Telefone configurado no ambiente."),
    PlaceholderDefinition("documento.data_emissao", "Data de emissão", "Documento", "Data atual no formato brasileiro."),
    PlaceholderDefinition("documento.local_emissao", "Local de emissão", "Documento", "Local informado no momento da geração."),
    PlaceholderDefinition("documento.numero", "Número do documento", "Documento", "Identificador único dentro do escopo do profissional."),
)

ALLOWED_PLACEHOLDERS = {definition.key for definition in PLACEHOLDER_DEFINITIONS}


def list_placeholders() -> list[dict[str, str]]:
    return [
        {
            "key": definition.key,
            "token": "{{" + definition.key + "}}",
            "label": definition.label,
            "group": definition.group,
            "description": definition.description,
        }
        for definition in PLACEHOLDER_DEFINITIONS
    ]


def extract_placeholders(content: str) -> set[str]:
    return set(PLACEHOLDER_PATTERN.findall(content or ""))


def validate_template_content(content: str) -> str:
    content = (content or "").strip()
    if not content:
        raise ValidationError("O conteúdo do template é obrigatório.")
    if len(content) > MAX_TEMPLATE_LENGTH:
        raise ValidationError(
            f"O conteúdo deve possuir no máximo {MAX_TEMPLATE_LENGTH} caracteres."
        )
    unknown = sorted(extract_placeholders(content) - ALLOWED_PLACEHOLDERS)
    if unknown:
        raise ValidationError(
            "Marcadores não reconhecidos: " + ", ".join(f"{{{{{item}}}}}" for item in unknown)
        )
    return content


def _format_date(value: date | None) -> str:
    return value.strftime("%d/%m/%Y") if value else ""


def build_document_context(*, patient, professional, document_number: str, local_emissao: str = "") -> dict[str, str]:
    """Monta apenas os valores explicitamente autorizados pela whitelist."""

    today = timezone.localdate()
    return {
        "paciente.nome": patient.display_name,
        "paciente.nome_completo": patient.full_name,
        "paciente.nome_social": patient.social_name or "",
        "paciente.cpf": patient.formatted_cpf,
        "paciente.data_nascimento": _format_date(patient.birth_date),
        "paciente.idade": str(patient.age) if patient.age is not None else "",
        "paciente.responsavel_nome": patient.guardian_name or "",
        "profissional.nome": professional.full_name,
        "profissional.registro_profissional": professional.crp_number or "",
        "profissional.especialidade": professional.specialty or "",
        "clinica.nome": getattr(settings, "DOCUMENT_CLINIC_NAME", "Elo Terapêutico"),
        "clinica.endereco": getattr(settings, "DOCUMENT_CLINIC_ADDRESS", ""),
        "clinica.telefone": getattr(settings, "DOCUMENT_CLINIC_PHONE", ""),
        "documento.data_emissao": _format_date(today),
        "documento.local_emissao": local_emissao.strip(),
        "documento.numero": document_number,
    }


def replace_placeholders(content: str, context: dict[str, Any]) -> str:
    validate_template_content(content)

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(context.get(key, ""))

    return PLACEHOLDER_PATTERN.sub(replace, content)


def render_safe_markdown(content: str, context: dict[str, Any]) -> str:
    """Renderizador deliberadamente limitado: sem HTML bruto, scripts ou avaliação dinâmica."""

    text = replace_placeholders(content, context)
    escaped = html.escape(text, quote=True)
    lines = escaped.splitlines()
    rendered: list[str] = []
    list_open = False

    def close_list() -> None:
        nonlocal list_open
        if list_open:
            rendered.append("</ul>")
            list_open = False

    for raw_line in lines:
        line = raw_line.strip()
        if line == "[[QUEBRA_DE_PAGINA]]":
            close_list()
            rendered.append('<div class="page-break"></div>')
            continue
        if line.startswith("### "):
            close_list()
            rendered.append(f"<h3>{line[4:]}</h3>")
            continue
        if line.startswith("## "):
            close_list()
            rendered.append(f"<h2>{line[3:]}</h2>")
            continue
        if line.startswith("# "):
            close_list()
            rendered.append(f"<h1>{line[2:]}</h1>")
            continue
        if line.startswith(("- ", "* ")):
            if not list_open:
                rendered.append("<ul>")
                list_open = True
            rendered.append(f"<li>{line[2:]}</li>")
            continue
        close_list()
        if not line:
            rendered.append("<p>&nbsp;</p>")
        else:
            rendered.append(f"<p>{line}</p>")

    close_list()
    output = "\n".join(rendered)
    output = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", output)
    output = re.sub(r"(?<!\*)\*(.+?)\*(?!\*)", r"<em>\1</em>", output)
    return output


def sample_document_context() -> dict[str, str]:
    return {
        "paciente.nome": "Nome do paciente",
        "paciente.nome_completo": "Nome completo do paciente",
        "paciente.nome_social": "",
        "paciente.cpf": "000.000.000-00",
        "paciente.data_nascimento": "01/01/2000",
        "paciente.idade": "26",
        "paciente.responsavel_nome": "Nome do responsável",
        "profissional.nome": "Nome do profissional",
        "profissional.registro_profissional": "00/000000",
        "profissional.especialidade": "Especialidade",
        "clinica.nome": getattr(settings, "DOCUMENT_CLINIC_NAME", "Elo Terapêutico"),
        "clinica.endereco": getattr(settings, "DOCUMENT_CLINIC_ADDRESS", ""),
        "clinica.telefone": getattr(settings, "DOCUMENT_CLINIC_PHONE", ""),
        "documento.data_emissao": _format_date(timezone.localdate()),
        "documento.local_emissao": "Cidade/UF",
        "documento.numero": "DOC-AAAA-000000",
    }
