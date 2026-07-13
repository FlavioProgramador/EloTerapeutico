from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
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


def main() -> None:
    errors: list[str] = []
    forbidden_directories = [ROOT / "core", BACKEND / "core", BACKEND / "elo_terapeutico"]
    for directory in forbidden_directories:
        if directory.exists():
            errors.append(f"Diretório legado ainda existe: {directory.relative_to(ROOT)}")

    required = [
        BACKEND / "apps" / "core" / "apps.py",
        BACKEND / "config" / "settings" / "base.py",
        BACKEND / "infrastructure" / "payments" / "asaas" / "client.py",
        BACKEND / "infrastructure" / "messaging" / "email.py",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"Arquivo obrigatório ausente: {path.relative_to(ROOT)}")

    banned_patterns = {
        r"(?m)^\s*from core(?:\.|\s+import)": "import legado from core",
        r"(?m)^\s*import core(?:\.|\s|$)": "import legado import core",
        r"elo_terapeutico\.": "referência ao pacote de configuração antigo",
        r"apps\.billing\.services\.gateways\.asaas": "client Asaas no domínio billing",
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
