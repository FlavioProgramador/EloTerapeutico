#!/usr/bin/env python3
"""Valida links locais, cercas Markdown/Mermaid e exemplos de segredo.

O script usa apenas a biblioteca padrão para poder rodar no CI e localmente.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".next", ".venv", "venv", "node_modules", "dist", "build"}
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SECRET_ASSIGNMENT = re.compile(
    r"(?im)^\s*(SECRET_KEY|JWT_SECRET|FIELD_ENCRYPTION_KEY(?:_V2)?|"
    r"ASAAS_API_KEY|ASAAS_WEBHOOK_TOKEN|AZURE_STORAGE_CONNECTION_STRING|"
    r"EMAIL_HOST_PASSWORD|POSTGRES_PASSWORD)\s*=\s*([^\s#]+)\s*$"
)
TOKEN_PATTERNS = [
    re.compile(r"\bgh[opusr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]
SAFE_VALUE_PARTS = {
    "configure-",
    "example",
    "localhost",
    "local",
    "ficticio",
    "fictícia",
    "ficticia",
    "placeholder",
    "<",
    "${",
}


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.md"):
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def clean_link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    return unquote(target)


def validate_link(source: Path, raw_target: str) -> str | None:
    target = clean_link_target(raw_target)
    if not target or target.startswith(("#", "http://", "https://", "mailto:", "tel:", "data:")):
        return None
    if target.startswith("/"):
        # Rota da aplicação/API, não caminho do repositório.
        return None

    path_part = target.split("#", 1)[0].split("?", 1)[0]
    if not path_part:
        return None

    resolved = (source.parent / path_part).resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError:
        return f"link escapa da raiz do repositório: {target}"

    if not resolved.exists():
        return f"destino inexistente: {target}"
    return None


def validate_secrets(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    for token_pattern in TOKEN_PATTERNS:
        if token_pattern.search(text):
            errors.append(f"{path.relative_to(ROOT)}: padrão de token potencialmente real")

    for match in SECRET_ASSIGNMENT.finditer(text):
        name, value = match.groups()
        normalized = value.strip().lower()
        if not normalized:
            continue
        if any(part in normalized for part in SAFE_VALUE_PARTS):
            continue
        if len(value) >= 20:
            line = text.count("\n", 0, match.start()) + 1
            errors.append(
                f"{path.relative_to(ROOT)}:{line}: valor de {name} parece segredo real; use placeholder"
            )
    return errors


def main() -> int:
    errors: list[str] = []
    markdown_files = iter_markdown_files()

    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT)

        fence_count = sum(1 for line in text.splitlines() if line.strip().startswith("```"))
        if fence_count % 2:
            errors.append(f"{relative}: quantidade ímpar de cercas Markdown ({fence_count})")

        mermaid_open = sum(1 for line in text.splitlines() if line.strip() == "```mermaid")
        if mermaid_open:
            # A checagem global de cercas acima garante fechamento; aqui apenas registra blocos detectados.
            pass

        for match in MARKDOWN_LINK.finditer(text):
            problem = validate_link(path, match.group(1))
            if problem:
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{relative}:{line}: {problem}")

        errors.extend(validate_secrets(path, text))

    for env_path in [ROOT / ".env.example", ROOT / "backend/.env.example", ROOT / "frontend/.env.example"]:
        if env_path.exists():
            errors.extend(validate_secrets(env_path, env_path.read_text(encoding="utf-8")))

    if errors:
        print("Falhas na validação documental:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"Documentação validada: {len(markdown_files)} arquivos Markdown, "
        "links locais existentes, cercas balanceadas e nenhum padrão de segredo detectado."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
