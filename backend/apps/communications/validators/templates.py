from __future__ import annotations

import re
from collections.abc import Mapping
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.utils.html import escape, linebreaks

from apps.communications.constants import (
    ALLOWED_TEMPLATE_VARIABLES,
    BLOCKED_CLINICAL_VARIABLES,
)

VARIABLE_RE = re.compile(r"{{\s*([a-zA-Z][a-zA-Z0-9_]*)\s*}}")
SCRIPT_RE = re.compile(r"<\s*(script|iframe|object|embed|style)\b", re.IGNORECASE)
EVENT_HANDLER_RE = re.compile(r"\son[a-z]+\s*=", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s<>]+", re.IGNORECASE)


def extract_template_variables(value: str) -> set[str]:
    return set(VARIABLE_RE.findall(value or ""))


def validate_template_text(subject: str, body: str) -> list[str]:
    if len(subject or "") > 255:
        raise ValidationError(
            {"subject_template": "O assunto deve ter no máximo 255 caracteres."}
        )
    if not body or not body.strip():
        raise ValidationError(
            {"body_template": "O conteúdo do template é obrigatório."}
        )
    if len(body) > 10000:
        raise ValidationError(
            {"body_template": "O conteúdo deve ter no máximo 10.000 caracteres."}
        )
    if SCRIPT_RE.search(body) or EVENT_HANDLER_RE.search(body):
        raise ValidationError(
            {"body_template": "HTML executável não é permitido."}
        )

    variables = extract_template_variables(f"{subject}\n{body}")
    blocked = variables & BLOCKED_CLINICAL_VARIABLES
    unknown = variables - ALLOWED_TEMPLATE_VARIABLES
    if blocked:
        raise ValidationError(
            {
                "body_template": (
                    "Variáveis clínicas não permitidas: "
                    f"{', '.join(sorted(blocked))}."
                )
            }
        )
    if unknown:
        raise ValidationError(
            {
                "body_template": (
                    "Variáveis desconhecidas: "
                    f"{', '.join(sorted(unknown))}."
                )
            }
        )

    for url in URL_RE.findall(body):
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValidationError(
                {"body_template": "O template contém uma URL insegura."}
            )
    return sorted(variables)


def render_template_text(value: str, variables: Mapping[str, object]) -> str:
    allowed = {
        key: str(variable_value)
        for key, variable_value in variables.items()
        if key in ALLOWED_TEMPLATE_VARIABLES
    }

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in allowed:
            raise ValidationError(
                f"A variável '{name}' não recebeu um valor válido."
            )
        return allowed[name]

    return VARIABLE_RE.sub(replace, value or "")


def plain_text_to_safe_html(value: str) -> str:
    return linebreaks(escape(value or ""), autoescape=False)
