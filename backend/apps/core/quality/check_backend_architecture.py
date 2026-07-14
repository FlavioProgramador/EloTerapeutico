from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BACKEND = ROOT / "backend"
TEXT_SUFFIXES = {".py", ".toml", ".ini", ".yml", ".yaml", ".sh"}
TEXT_FILENAMES = {"Dockerfile", "Makefile", "Procfile"}
SKIP_PARTS = {".git", "node_modules", ".next", "dist", "build", ".venv", "venv"}


def iter_source_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.name in TEXT_FILENAMES or path.suffix.lower() in TEXT_SUFFIXES:
            yield path


ALLOWED_BACKEND_ROOT_DIRECTORIES = {"apps", "config"}
IGNORED_LOCAL_DIRECTORIES = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "media",
    "staticfiles",
    "test-media",
    ".test-media",
    "venv",
    ".venv",
}


def validate_backend_root_directories(errors: list[str]) -> None:
    for child in BACKEND.iterdir():
        if not child.is_dir():
            continue
        if child.name in ALLOWED_BACKEND_ROOT_DIRECTORIES or child.name in IGNORED_LOCAL_DIRECTORIES:
            continue
        errors.append(
            "Diretório versionado inesperado na raiz do backend: "
            f"{child.relative_to(ROOT)}. Mova-o para apps/ ou config/."
        )


def validate_removed_layer_paths(errors: list[str]) -> None:
    apps_root = BACKEND / "apps"
    for path in apps_root.rglob("*"):
        if path.is_dir() and path.name == "model_parts":
            errors.append(f"Diretório legado model_parts ainda existe: {path.relative_to(ROOT)}")
        if path.is_file() and path.name == "core_services.py":
            errors.append(f"Service monolítico legado ainda existe: {path.relative_to(ROOT)}")


def main() -> None:
    errors: list[str] = []
    validate_backend_root_directories(errors)
    validate_removed_layer_paths(errors)
    forbidden_directories = [ROOT / "core", BACKEND / "core", BACKEND / "elo_terapeutico"]
    for directory in forbidden_directories:
        if directory.exists():
            errors.append(f"Diretório legado ainda existe: {directory.relative_to(ROOT)}")

    required = [
        BACKEND / "apps" / "core" / "apps.py",
        BACKEND / "config" / "settings" / "base.py",
        BACKEND / "apps" / "billing" / "infrastructure" / "payments" / "asaas" / "client.py",
        BACKEND / "apps" / "communications" / "infrastructure" / "messaging" / "email.py",
        BACKEND / "apps" / "documents" / "models" / "__init__.py",
        BACKEND / "apps" / "documents" / "services" / "generated_documents.py",
        BACKEND / "apps" / "documents" / "selectors" / "document_templates.py",
        BACKEND / "apps" / "reports" / "services" / "financial_reports.py",
        BACKEND / "apps" / "reports" / "selectors" / "appointments.py",
        BACKEND / "apps" / "agenda" / "services" / "appointments.py",
        BACKEND / "apps" / "agenda" / "selectors" / "appointments.py",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"Arquivo obrigatório ausente: {path.relative_to(ROOT)}")

    banned_patterns = {
        r"(?m)^\s*from core(?:\.|\s+import)": "import legado from core",
        r"(?m)^\s*import core(?:\.|\s|$)": "import legado import core",
        r"elo_terapeutico\.": "referência ao pacote de configuração antigo",
        r"apps\.billing\.services\.gateways\.asaas": "client Asaas no domínio billing",
        r"\.model_parts(?:\.|\s+import)": "import para pacote model_parts removido",
        r"\.services\.core_services(?:\s+import|\.)": "import para service monolítico removido",
    }
    for path in iter_source_files():
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern, description in banned_patterns.items():
            if re.search(pattern, content):
                errors.append(f"{description}: {path.relative_to(ROOT)}")

    billing_http_modules = [
        BACKEND / "apps" / "billing" / "views.py",
        BACKEND / "apps" / "billing" / "checkout_views.py",
    ]
    for path in billing_http_modules:
        if not path.exists():
            errors.append(f"Módulo HTTP de billing ausente: {path.relative_to(ROOT)}")
            continue
        content = path.read_text(encoding="utf-8")
        if re.search(r"(?m)^\s*(?:from|import) infrastructure(?:\.|\s|$)", content):
            errors.append(f"view de billing importa infrastructure diretamente: {path.relative_to(ROOT)}")
        if re.search(r"\b[A-Z][A-Za-z0-9_]*\.objects\b", content):
            errors.append(f"view de billing acessa ORM diretamente: {path.relative_to(ROOT)}")

    core_apps = []
    base_settings = BACKEND / "config" / "settings" / "base.py"
    if base_settings.exists():
        content = base_settings.read_text(encoding="utf-8")
        core_apps = re.findall(r'["\']([^"\']*core[^"\']*)["\']', content)
        if '"apps.core.apps.CoreConfig"' not in content:
            errors.append("CoreConfig canônico não está registrado em INSTALLED_APPS")
    if sum(value.endswith("CoreConfig") for value in core_apps) != 1:
        errors.append(f"Esperado exatamente um CoreConfig; encontrados: {core_apps}")

    if errors:
        raise SystemExit("Falhas de arquitetura:\n- " + "\n- ".join(sorted(set(errors))))
    print("Arquitetura do backend validada com sucesso.")


if __name__ == "__main__":
    main()
