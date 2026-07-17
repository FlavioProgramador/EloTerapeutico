from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BACKEND = ROOT / "backend"
TEXT_SUFFIXES = {".py", ".toml", ".ini", ".yml", ".yaml", ".sh"}
TEXT_FILENAMES = {"Dockerfile", "Makefile", "Procfile"}
SKIP_PARTS = {
    ".git",
    "node_modules",
    ".next",
    "dist",
    "build",
    ".venv",
    "venv",
}


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
        if (
            child.name in ALLOWED_BACKEND_ROOT_DIRECTORIES
            or child.name in IGNORED_LOCAL_DIRECTORIES
        ):
            continue
        errors.append(
            "Diretório versionado inesperado na raiz do backend: "
            f"{child.relative_to(ROOT)}. Mova-o para apps/ ou config/."
        )


def validate_removed_layer_paths(errors: list[str]) -> None:
    apps_root = BACKEND / "apps"
    for path in apps_root.rglob("*"):
        if path.is_dir() and path.name == "model_parts":
            errors.append(
                f"Diretório legado model_parts ainda existe: {path.relative_to(ROOT)}"
            )
        if path.is_file() and path.name == "core_services.py":
            errors.append(
                f"Service monolítico legado ainda existe: {path.relative_to(ROOT)}"
            )


def validate_thin_facades(
    errors: list[str],
    *,
    app_name: str,
    paths: list[Path],
    max_lines: int = 80,
) -> None:
    for path in paths:
        if not path.exists():
            errors.append(
                f"Fachada de compatibilidade de {app_name} ausente: "
                f"{path.relative_to(ROOT)}"
            )
            continue
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > max_lines:
            errors.append(
                f"Fachada de compatibilidade de {app_name} contém "
                f"implementação excessiva: {path.relative_to(ROOT)} "
                f"({line_count} linhas)"
            )


def validate_communications_architecture(errors: list[str]) -> None:
    app_root = BACKEND / "apps" / "communications"
    required_paths = [
        app_root / "api" / "v1" / "urls.py",
        app_root / "api" / "v1" / "serializers" / "__init__.py",
        app_root / "api" / "v1" / "permissions" / "__init__.py",
        app_root / "api" / "public" / "urls.py",
        app_root / "admin" / "__init__.py",
        app_root / "integrations" / "providers" / "__init__.py",
        app_root / "selectors" / "__init__.py",
        app_root / "signals" / "__init__.py",
        app_root / "tasks" / "__init__.py",
        app_root / "validators" / "__init__.py",
        app_root / "migration_operations.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(
                "Estrutura obrigatória de communications ausente: "
                f"{path.relative_to(ROOT)}"
            )

    forbidden_monoliths = [
        app_root / "admin.py",
        app_root / "selectors.py",
        app_root / "signals.py",
        app_root / "tasks.py",
        app_root / "validators.py",
    ]
    for path in forbidden_monoliths:
        if path.exists():
            errors.append(
                "Módulo monolítico de communications retornou à raiz: "
                f"{path.relative_to(ROOT)}"
            )

    validate_thin_facades(
        errors,
        app_name="communications",
        paths=[
            app_root / "channel_serializers.py",
            app_root / "permissions.py",
            app_root / "providers.py",
            app_root / "serializers.py",
            app_root / "urls.py",
            app_root / "urls_public.py",
        ],
    )

    tasks_init = app_root / "tasks" / "__init__.py"
    if tasks_init.exists():
        tasks_source = tasks_init.read_text(encoding="utf-8")
        required_task_exports = {
            "send_communication",
            "dispatch_due_communications",
            "schedule_operational_automations_task",
            "cleanup_expired_public_tokens",
            "send_notification_delivery",
            "cleanup_expired_notifications",
        }
        for task_name in required_task_exports:
            if task_name not in tasks_source:
                errors.append(
                    "Task de communications não é exportada para autodiscovery: "
                    f"{task_name}"
                )


def validate_billing_architecture(errors: list[str]) -> None:
    app_root = BACKEND / "apps" / "billing"
    required_paths = [
        app_root / "models" / "__init__.py",
        app_root / "api" / "v1" / "urls.py",
        app_root / "api" / "v1" / "serializers" / "__init__.py",
        app_root / "api" / "v1" / "views" / "__init__.py",
        app_root / "api" / "v1" / "permissions" / "__init__.py",
        app_root / "api" / "public" / "registration.py",
        app_root / "api" / "public" / "webhooks.py",
        app_root / "api" / "legacy" / "routes.py",
        app_root / "api" / "legacy" / "urls.py",
        app_root / "admin" / "__init__.py",
        app_root / "authentication" / "__init__.py",
        app_root / "checks" / "__init__.py",
        app_root / "security" / "__init__.py",
        app_root / "tasks" / "__init__.py",
        app_root / "views" / "__init__.py",
        app_root
        / "integrations"
        / "webhooks"
        / "asaas"
        / "__init__.py",
        app_root
        / "infrastructure"
        / "payments"
        / "asaas"
        / "client.py",
        app_root / "selectors" / "catalog.py",
        app_root / "selectors" / "orders.py",
        app_root / "selectors" / "payments.py",
        app_root / "services" / "checkout.py",
        app_root / "services" / "orders.py",
        app_root / "services" / "subscriptions.py",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append(
                "Estrutura obrigatória de billing ausente: "
                f"{path.relative_to(ROOT)}"
            )

    forbidden_root_files = [
        "access_views.py",
        "admin.py",
        "authentication.py",
        "checkout_views.py",
        "checks.py",
        "decorators.py",
        "legacy_route.py",
        "legacy_urls.py",
        "models.py",
        "permissions.py",
        "registration.py",
        "security.py",
        "serializers.py",
        "tasks.py",
        "urls.py",
        "views.py",
    ]
    for filename in forbidden_root_files:
        path = app_root / filename
        if path.exists():
            errors.append(
                "Arquivo de implementação ou compatibilidade retornou à raiz de "
                f"billing: {path.relative_to(ROOT)}"
            )

    allowed_root_files = {"__init__.py", "apps.py", "README.md"}
    for path in app_root.iterdir():
        if not path.is_file() or path.name in allowed_root_files:
            continue
        errors.append(
            "Arquivo inesperado na raiz de billing: "
            f"{path.relative_to(ROOT)}. Organize-o em uma camada/pasta."
        )

    validate_thin_facades(
        errors,
        app_name="billing",
        paths=[
            app_root / "authentication" / "__init__.py",
            app_root / "views" / "__init__.py",
            app_root / "webhooks" / "asaas.py",
        ],
    )

    tasks_init = app_root / "tasks" / "__init__.py"
    if tasks_init.exists():
        tasks_source = tasks_init.read_text(encoding="utf-8")
        for task_name in {
            "process_webhook_event_task",
            "dispatch_pending_webhook_events",
            "reconcile_asaas_payments",
        }:
            if task_name not in tasks_source:
                errors.append(
                    "Task de billing não é exportada para autodiscovery: "
                    f"{task_name}"
                )

    canonical_views = app_root / "api" / "v1" / "views"
    if canonical_views.exists():
        for path in canonical_views.glob("*.py"):
            content = path.read_text(encoding="utf-8")
            if re.search(
                r"(?m)^\s*(?:from|import) "
                r"apps\.billing\.infrastructure(?:\.|\s|$)",
                content,
            ):
                errors.append(
                    "view de billing importa infrastructure diretamente: "
                    f"{path.relative_to(ROOT)}"
                )
            if re.search(r"\b[A-Z][A-Za-z0-9_]*\.objects\b", content):
                errors.append(
                    "view de billing acessa ORM diretamente: "
                    f"{path.relative_to(ROOT)}"
                )


def main() -> None:
    errors: list[str] = []
    validate_backend_root_directories(errors)
    validate_removed_layer_paths(errors)
    validate_communications_architecture(errors)
    validate_billing_architecture(errors)

    forbidden_directories = [
        ROOT / "core",
        BACKEND / "core",
        BACKEND / "elo_terapeutico",
    ]
    for directory in forbidden_directories:
        if directory.exists():
            errors.append(
                f"Diretório legado ainda existe: {directory.relative_to(ROOT)}"
            )

    required = [
        BACKEND / "apps" / "core" / "apps.py",
        BACKEND / "config" / "settings" / "base.py",
        BACKEND
        / "apps"
        / "communications"
        / "infrastructure"
        / "messaging"
        / "email.py",
        BACKEND / "apps" / "documents" / "models" / "__init__.py",
        BACKEND
        / "apps"
        / "documents"
        / "services"
        / "generated_documents.py",
        BACKEND
        / "apps"
        / "documents"
        / "selectors"
        / "document_templates.py",
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
        r"apps\.billing\.services\.gateways\.asaas": (
            "client Asaas no domínio billing"
        ),
        r"\.model_parts(?:\.|\s+import)": "import para pacote model_parts removido",
        r"\.services\.core_services(?:\s+import|\.)": (
            "import para service monolítico removido"
        ),
    }
    for path in iter_source_files():
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern, description in banned_patterns.items():
            if re.search(pattern, content):
                errors.append(f"{description}: {path.relative_to(ROOT)}")

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
        raise SystemExit(
            "Falhas de arquitetura:\n- " + "\n- ".join(sorted(set(errors)))
        )
    print("Arquitetura do backend validada com sucesso.")


if __name__ == "__main__":
    main()
