#!/usr/bin/env python3
"""Valida links, Markdown, segredos e consistência da documentação.

A validação usa somente a biblioteca padrão. Arquivos JSON e Python são lidos
com parsers próprios. O Docker Compose é validado de forma autoritativa pelo
workflow com ``docker compose config``; neste script, uma leitura restrita da
seção top-level ``services`` permite execução local sem Docker ou PyYAML.
"""

from __future__ import annotations

import ast
import json
import re
import shlex
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".next", ".venv", "venv", "node_modules", "dist", "build"}
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
ENV_ASSIGNMENT = re.compile(r"^[ \t]*([A-Z][A-Z0-9_]*)[ \t]*=", re.MULTILINE)
SECRET_ASSIGNMENT = re.compile(
    r"(?im)^[ \t]*(SECRET_KEY|JWT_SECRET|FIELD_ENCRYPTION_KEY(?:_V2)?|"
    r"ASAAS_API_KEY|ASAAS_WEBHOOK_TOKEN|AZURE_STORAGE_CONNECTION_STRING|"
    r"EMAIL_HOST_PASSWORD|POSTGRES_PASSWORD|REDIS_PASSWORD|LIVEKIT_API_SECRET|"
    r"WHATSAPP_ACCESS_TOKEN|WHATSAPP_WEBHOOK_VERIFY_TOKEN|WHATSAPP_APP_SECRET|"
    r"SMS_API_KEY)[ \t]*=[ \t]*([^ \t\r\n#]*)[ \t]*(?:#.*)?$"
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

CANONICAL_FILES = [
    "README.md",
    "docs/README.md",
    "docs/02-arquitetura/filas-e-processamento-assincrono.md",
    "docs/03-instalacao/instalacao-docker.md",
    "docs/04-configuracao/variaveis-de-ambiente.md",
    "docs/05-modulos/README.md",
    "docs/05-modulos/organizacoes/README.md",
    "docs/05-modulos/comunicacoes/README.md",
    "docs/07-api/README.md",
    "docs/12-operacao/docker-e-workers.md",
    "docs/17-referencia/status-do-projeto.md",
    "docs/17-referencia/matriz-de-modulos.md",
    "docs/17-referencia/matriz-de-integracoes.md",
    "docs/17-referencia/matriz-de-containers.md",
    "docs/17-referencia/inventario-tecnologico.md",
]

APP_DOC_TOKENS = {
    "core": ("| Core |", "apps/core", "apps.core"),
    "users": ("Autenticação e usuários", "apps/users", "apps.users"),
    "organizations": ("Organizações e multi-tenancy", "apps/organizations", "apps.organizations"),
    "patients": ("Pacientes", "apps/patients", "apps.patients"),
    "records": ("Prontuário", "apps/records", "apps.records"),
    "scheduling": ("Agenda e scheduling", "apps/scheduling", "apps.scheduling"),
    "finances": ("Financeiro clínico", "apps/finances", "apps.finances"),
    "documents": ("Documentos", "apps/documents", "apps.documents"),
    "reports": ("Relatórios", "apps/reports", "apps.reports"),
    "forms": ("Formulários", "apps/forms", "apps.forms"),
    "billing": ("Billing SaaS", "apps/billing", "apps.billing"),
    "communications": ("Comunicações", "apps/communications", "apps.communications"),
    "audit": ("Auditoria", "apps/audit", "apps.audit"),
}

REQUIRED_TOP_LEVEL_ROUTES = {
    "/api/schema/",
    "/api/docs/",
    "/api/redoc/",
    "/api/health/",
    "/health/live/",
    "/health/ready/",
}


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*.md"):
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def read_text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


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


def validate_canonical_files() -> list[str]:
    return [f"arquivo canônico ausente: {relative}" for relative in CANONICAL_FILES if not (ROOT / relative).exists()]


def parse_compose_services() -> set[str]:
    """Lê apenas as chaves imediatamente abaixo de ``services:``.

    O workflow também executa ``docker compose config --services``, que é a
    validação autoritativa do YAML e da interpolação.
    """

    compose = ROOT / "docker-compose.yml"
    services: set[str] = set()
    in_services = False
    for raw_line in compose.read_text(encoding="utf-8").splitlines():
        if raw_line.strip() == "services":
            in_services = True
            continue
        if in_services and raw_line and not raw_line.startswith(" "):
            break
        if not in_services:
            continue
        match = re.match(r"^  ([A-Za-z0-9_.-]+):\s*$", raw_line)
        if match:
            services.add(match.group(1))
    return services


def validate_container_matrix(services: set[str]) -> list[str]:
    matrix_path = ROOT / "docs/17-referencia/matriz-de-containers.md"
    if not matrix_path.exists():
        return ["matriz de containers ausente"]
    text = matrix_path.read_text(encoding="utf-8")
    return [
        f"docs/17-referencia/matriz-de-containers.md: serviço não documentado: {service}"
        for service in sorted(services)
        if f"`{service}`" not in text
    ]


def extract_compose_service_from_command(line: str) -> str | None:
    if "docker compose" not in line:
        return None
    lowered = line.casefold()
    if "não use" in lowered or "nao use" in lowered or "inexistente" in lowered:
        return None

    candidate = line.strip().strip("`")
    try:
        tokens = shlex.split(candidate)
    except ValueError:
        return None
    try:
        compose_index = tokens.index("compose")
    except ValueError:
        return None
    if compose_index == 0 or tokens[compose_index - 1] != "docker":
        return None
    if len(tokens) <= compose_index + 1:
        return None

    subcommand = tokens[compose_index + 1]
    if subcommand not in {"logs", "restart", "exec", "stop", "start", "kill", "rm"}:
        return None

    index = compose_index + 2
    while index < len(tokens) and tokens[index].startswith("-"):
        index += 1
    if index >= len(tokens):
        return None

    service = tokens[index]
    if service.startswith(("<", "${")):
        return None
    return service


def validate_docker_commands(markdown_files: list[Path], services: set[str]) -> list[str]:
    errors: list[str] = []
    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            service = extract_compose_service_from_command(line)
            if service and service not in services:
                errors.append(
                    f"{path.relative_to(ROOT)}:{line_number}: comando usa serviço Docker inexistente: {service}"
                )
    return errors


def parse_local_apps() -> set[str]:
    base_path = ROOT / "backend/config/settings/base.py"
    tree = ast.parse(base_path.read_text(encoding="utf-8"), filename=str(base_path))
    apps: set[str] = set()

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "LOCAL_APPS" for target in node.targets):
            continue
        if not isinstance(node.value, (ast.List, ast.Tuple)):
            continue
        for element in node.value.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                value = element.value
                if value.startswith("apps."):
                    apps.add(value.split(".", 2)[1])

    production_text = read_text("backend/config/settings/production.py")
    if "apps.organizations.apps.OrganizationsConfig" in production_text:
        apps.add("organizations")
    return apps


def validate_module_matrix(apps: set[str]) -> list[str]:
    matrix = read_text("docs/17-referencia/matriz-de-modulos.md")
    errors: list[str] = []
    for app in sorted(apps):
        tokens = APP_DOC_TOKENS.get(app, (f"apps/{app}", f"apps.{app}", app))
        if not any(token.casefold() in matrix.casefold() for token in tokens):
            errors.append(f"matriz de módulos não representa o app Django: {app}")
    return errors


def parse_api_prefixes() -> set[str]:
    urls_path = ROOT / "backend/config/urls.py"
    tree = ast.parse(urls_path.read_text(encoding="utf-8"), filename=str(urls_path))
    prefixes: set[str] = set()

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "api_v1_patterns" for target in node.targets):
            continue
        if not isinstance(node.value, ast.List):
            continue
        for element in node.value.elts:
            if not isinstance(element, ast.Call) or not element.args:
                continue
            first_arg = element.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                prefixes.add(f"/api/v1/{first_arg.value}")
    return prefixes


def validate_api_reference(prefixes: set[str]) -> list[str]:
    api_doc = read_text("docs/07-api/README.md")
    errors = [f"docs/07-api/README.md: prefixo ausente: {prefix}" for prefix in sorted(prefixes) if prefix not in api_doc]
    for route in sorted(REQUIRED_TOP_LEVEL_ROUTES):
        if route not in api_doc:
            errors.append(f"docs/07-api/README.md: rota top-level ausente: {route}")
    return errors


def parse_env_names(path: Path) -> set[str]:
    return set(ENV_ASSIGNMENT.findall(path.read_text(encoding="utf-8")))


def validate_environment_reference() -> list[str]:
    env_paths = [ROOT / ".env.example", ROOT / "backend/.env.example", ROOT / "frontend/.env.example"]
    names: set[str] = set()
    for path in env_paths:
        if path.exists():
            names.update(parse_env_names(path))

    reference = read_text("docs/04-configuracao/variaveis-de-ambiente.md")
    return [
        f"docs/04-configuracao/variaveis-de-ambiente.md: variável não documentada: {name}"
        for name in sorted(names)
        if name not in reference
    ]


def requirement_specifications() -> dict[str, str]:
    expected = {
        "Django",
        "djangorestframework",
        "celery",
        "livekit-api",
        "django-unfold",
        "weasyprint",
    }
    specs: dict[str, str] = {}
    for raw_line in read_text("backend/requirements.txt").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        for package in expected:
            if line.startswith(package) and line[len(package) : len(package) + 1] in {"<", ">", "=", "!", "~"}:
                specs[package] = line[len(package) :]
    return specs


def validate_technology_inventory() -> list[str]:
    inventory = read_text("docs/17-referencia/inventario-tecnologico.md")
    package_json = json.loads(read_text("frontend/package.json"))
    dependencies = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}

    expected_frontend = {
        "next": dependencies["next"],
        "react": dependencies["react"],
        "react-dom": dependencies["react-dom"],
        "typescript": dependencies["typescript"],
        "tailwindcss": dependencies["tailwindcss"],
    }

    errors: list[str] = []
    for package, raw_version in expected_frontend.items():
        version = raw_version.lstrip("^~>=< ")
        if version not in inventory:
            errors.append(f"inventário tecnológico não contém a versão de {package}: {raw_version}")

    for package, spec in requirement_specifications().items():
        if spec not in inventory:
            errors.append(f"inventário tecnológico não contém a faixa de {package}: {spec}")

    image_expectations = {
        "backend/Dockerfile": (("python:3.12-slim", "python:3.12-slim-bookworm", "python:3.12-alpine"), "3.12"),
        "frontend/Dockerfile": (("node:24-alpine",), "24"),
        "docker-compose.yml": (("postgres:15-alpine",), "15"),
        "docker-compose.yml#redis": (("redis:7-alpine",), "7"),
    }
    compose_text = read_text("docker-compose.yml")
    for source, (images, version) in image_expectations.items():
        if source.startswith("backend/"):
            source_text = read_text("backend/Dockerfile")
        elif source.startswith("frontend/"):
            source_text = read_text("frontend/Dockerfile")
        else:
            source_text = compose_text
        if not any(image in source_text for image in images):
            errors.append(f"imagem esperada não encontrada em {source}: {images[0]}")
        if version not in inventory:
            errors.append(f"inventário tecnológico não contém versão de runtime/imagem: {version}")
    return errors


def extract_audit_commit(text: str) -> str | None:
    match = re.search(r"(?i)commit-base[^0-9a-f]*`([0-9a-f]{40})`", text)
    return match.group(1) if match else None


def validate_audit_metadata() -> list[str]:
    files = ["README.md", "docs/README.md", "docs/17-referencia/status-do-projeto.md"]
    values: dict[str, str] = {}
    errors: list[str] = []
    for relative in files:
        commit = extract_audit_commit(read_text(relative))
        if commit is None:
            errors.append(f"{relative}: metadado commit-base ausente ou inválido")
        else:
            values[relative] = commit
    if len(set(values.values())) > 1:
        rendered = ", ".join(f"{path}={sha}" for path, sha in values.items())
        errors.append(f"commit-base divergente entre documentos canônicos: {rendered}")
    return errors


def main() -> int:
    errors: list[str] = []
    markdown_files = iter_markdown_files()

    errors.extend(validate_canonical_files())

    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT)

        fence_count = sum(1 for line in text.splitlines() if line.strip().startswith("```") )
        if fence_count % 2:
            errors.append(f"{relative}: quantidade ímpar de cercas Markdown ({fence_count})")

        for match in MARKDOWN_LINK.finditer(text):
            problem = validate_link(path, match.group(1))
            if problem:
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{relative}:{line}: {problem}")

        errors.extend(validate_secrets(path, text))

    env_paths = [ROOT / ".env.example", ROOT / "backend/.env.example", ROOT / "frontend/.env.example"]
    for env_path in env_paths:
        if env_path.exists():
            errors.extend(validate_secrets(env_path, env_path.read_text(encoding="utf-8")))

    services = parse_compose_services()
    if not services:
        errors.append("docker-compose.yml: nenhum serviço foi identificado")
    else:
        errors.extend(validate_container_matrix(services))
        errors.extend(validate_docker_commands(markdown_files, services))

    errors.extend(validate_module_matrix(parse_local_apps()))
    errors.extend(validate_api_reference(parse_api_prefixes()))
    errors.extend(validate_environment_reference())
    errors.extend(validate_technology_inventory())
    errors.extend(validate_audit_metadata())

    if errors:
        print("Falhas na validação documental:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "Documentação validada: "
        f"{len(markdown_files)} arquivos Markdown, "
        f"{len(services)} serviços Docker, "
        "links locais existentes, cercas balanceadas, exemplos sem segredo aparente "
        "e referências estruturais sincronizadas."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())