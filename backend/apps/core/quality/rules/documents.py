"""Regras arquiteturais dedicadas ao app documents."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
BACKEND = ROOT / "backend"
DOCUMENTS = BACKEND / "apps" / "documents"


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _python_sources(root: Path):
    for path in root.rglob("*.py"):
        if "migrations" in path.parts or "__pycache__" in path.parts:
            continue
        yield path


def _validate_required_paths(errors: list[str]) -> None:
    required = [
        DOCUMENTS / "README.md",
        DOCUMENTS / "admin" / "__init__.py",
        DOCUMENTS / "admin" / "document_sequences.py",
        DOCUMENTS / "admin" / "document_templates.py",
        DOCUMENTS / "admin" / "generated_documents.py",
        DOCUMENTS / "api" / "v1" / "urls.py",
        DOCUMENTS / "api" / "v1" / "permissions" / "clinical_documents.py",
        DOCUMENTS / "api" / "v1" / "serializers" / "document_templates.py",
        DOCUMENTS / "api" / "v1" / "serializers" / "generated_documents.py",
        DOCUMENTS / "api" / "v1" / "serializers" / "previews.py",
        DOCUMENTS / "api" / "v1" / "views" / "document_templates.py",
        DOCUMENTS / "api" / "v1" / "views" / "generated_documents.py",
        DOCUMENTS / "api" / "v1" / "views" / "placeholders.py",
        DOCUMENTS / "exceptions" / "domain.py",
        DOCUMENTS / "infrastructure" / "pdf" / "renderer.py",
        DOCUMENTS / "models" / "generated.py",
        DOCUMENTS / "models" / "sequences.py",
        DOCUMENTS / "models" / "templates.py",
        DOCUMENTS / "selectors" / "document_templates.py",
        DOCUMENTS / "selectors" / "generated_documents.py",
        DOCUMENTS / "selectors" / "patients.py",
        DOCUMENTS / "services" / "document_templates.py",
        DOCUMENTS / "services" / "generated_documents.py",
        DOCUMENTS / "services" / "pdf_generation.py",
        DOCUMENTS / "services" / "placeholders.py",
        DOCUMENTS / "services" / "sequences.py",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"Estrutura obrigatória de documents ausente: {_relative(path)}")


def _validate_root(errors: list[str]) -> None:
    forbidden = {
        "admin.py",
        "exceptions.py",
        "filters.py",
        "models.py",
        "permissions.py",
        "selectors.py",
        "serializers.py",
        "services.py",
        "tasks.py",
        "views.py",
    }
    for name in forbidden:
        path = DOCUMENTS / name
        if path.exists():
            errors.append(f"Módulo monolítico retornou à raiz de documents: {_relative(path)}")

    allowed_root_files = {"README.md", "__init__.py", "apps.py", "urls.py"}
    for path in DOCUMENTS.iterdir():
        if path.is_file() and path.name not in allowed_root_files:
            errors.append(f"Arquivo inesperado na raiz de documents: {_relative(path)}")


def _validate_facades(errors: list[str]) -> None:
    facades = [
        DOCUMENTS / "urls.py",
        DOCUMENTS / "permissions" / "__init__.py",
        DOCUMENTS / "permissions" / "clinical_documents.py",
        DOCUMENTS / "serializers" / "__init__.py",
        DOCUMENTS / "serializers" / "document_templates.py",
        DOCUMENTS / "serializers" / "generated_documents.py",
        DOCUMENTS / "serializers" / "previews.py",
        DOCUMENTS / "views" / "__init__.py",
        DOCUMENTS / "views" / "document_templates.py",
        DOCUMENTS / "views" / "generated_documents.py",
        DOCUMENTS / "views" / "placeholders.py",
    ]
    for path in facades:
        if not path.exists():
            errors.append(f"Fachada de compatibilidade ausente: {_relative(path)}")
            continue
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > 40:
            errors.append(
                "Fachada de compatibilidade contém implementação excessiva: "
                f"{_relative(path)} ({line_count} linhas)"
            )


def _validate_views(errors: list[str]) -> None:
    views_root = DOCUMENTS / "api" / "v1" / "views"
    for path in views_root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if re.search(r"\b[A-Z][A-Za-z0-9_]*\.objects\b", source):
            errors.append(f"View de documents acessa ORM diretamente: {_relative(path)}")
        if ".delete(" in source:
            errors.append(f"View de documents exclui model diretamente: {_relative(path)}")
        if re.search(r"(?m)^\s*(?:from|import)\s+.*infrastructure", source):
            errors.append(f"View de documents importa infraestrutura diretamente: {_relative(path)}")
        if "weasyprint" in source or re.search(r"\bHTML\(", source):
            errors.append(f"View de documents renderiza PDF diretamente: {_relative(path)}")


def _validate_serializers(errors: list[str]) -> None:
    serializers_root = DOCUMENTS / "api" / "v1" / "serializers"
    forbidden_tokens = ("weasyprint", "default_storage", "FileResponse", "ContentFile")
    for path in serializers_root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token in source:
                errors.append(
                    f"Serializer de documents depende de infraestrutura ({token}): {_relative(path)}"
                )


def _validate_dependency_direction(errors: list[str]) -> None:
    layer_rules = {
        "models": ("apps.documents.api", "apps.documents.views", "apps.documents.serializers", "apps.documents.services"),
        "selectors": ("apps.documents.api", "apps.documents.views", "apps.documents.serializers", "apps.documents.services"),
        "services": ("apps.documents.api", "apps.documents.views", "apps.documents.serializers"),
        "infrastructure": ("apps.documents.api", "apps.documents.views", "apps.documents.serializers", "apps.documents.services"),
    }
    for layer, forbidden_imports in layer_rules.items():
        root = DOCUMENTS / layer
        if not root.exists():
            continue
        for path in _python_sources(root):
            source = path.read_text(encoding="utf-8")
            for imported in forbidden_imports:
                if imported in source:
                    errors.append(
                        f"Direção de dependência inválida em documents ({layer} -> {imported}): {_relative(path)}"
                    )


def _validate_exports(errors: list[str]) -> None:
    public_inits = [
        DOCUMENTS / "admin" / "__init__.py",
        DOCUMENTS / "api" / "v1" / "permissions" / "__init__.py",
        DOCUMENTS / "api" / "v1" / "serializers" / "__init__.py",
        DOCUMENTS / "api" / "v1" / "views" / "__init__.py",
        DOCUMENTS / "exceptions" / "__init__.py",
        DOCUMENTS / "models" / "__init__.py",
        DOCUMENTS / "selectors" / "__init__.py",
        DOCUMENTS / "services" / "__init__.py",
    ]
    for path in public_inits:
        if not path.exists():
            continue
        source = path.read_text(encoding="utf-8")
        if "import *" in source:
            errors.append(f"Export público usa import curinga: {_relative(path)}")
        if "__all__" not in source:
            errors.append(f"Export público sem __all__ explícito: {_relative(path)}")

    for path in _python_sources(DOCUMENTS):
        if "import *" in path.read_text(encoding="utf-8"):
            errors.append(f"Import curinga encontrado em documents: {_relative(path)}")


def _validate_routes(errors: list[str]) -> None:
    config_urls = BACKEND / "config" / "urls.py"
    source = config_urls.read_text(encoding="utf-8") if config_urls.exists() else ""
    if 'include("apps.documents.api.v1.urls")' not in source:
        errors.append("Roteamento global não utiliza apps.documents.api.v1.urls")
    if 'include("apps.documents.urls")' in source:
        errors.append("Roteamento global ainda utiliza a fachada legada apps.documents.urls")

    legacy_urls = DOCUMENTS / "urls.py"
    if legacy_urls.exists():
        legacy_source = legacy_urls.read_text(encoding="utf-8")
        if "from apps.documents.api.v1.urls import urlpatterns" not in legacy_source:
            errors.append("apps.documents.urls não é uma fachada fina para a API v1")


def validate_documents_architecture(errors: list[str]) -> None:
    """Acrescenta violações arquiteturais específicas do módulo documents."""

    _validate_required_paths(errors)
    _validate_root(errors)
    _validate_facades(errors)
    _validate_views(errors)
    _validate_serializers(errors)
    _validate_dependency_direction(errors)
    _validate_exports(errors)
    _validate_routes(errors)
