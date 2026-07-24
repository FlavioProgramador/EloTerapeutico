#!/usr/bin/env python3
"""Wrapper de validação documental com correção pontual do parser de Compose."""

from __future__ import annotations

import importlib.util
import pathlib
import re
import shlex
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate_docs.py"

spec = importlib.util.spec_from_file_location("validate_docs_module", MODULE_PATH)
if spec is None or spec.loader is None:
    raise SystemExit(f"Não foi possível carregar {MODULE_PATH}")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def parse_compose_services() -> set[str]:
    """Lê apenas as chaves imediatamente abaixo de ``services:``."""

    compose = ROOT / "docker-compose.yml"
    services: set[str] = set()
    in_services = False
    for raw_line in compose.read_text(encoding="utf-8").splitlines():
        if raw_line.strip() == "services:":
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


module.parse_compose_services = parse_compose_services
raise SystemExit(module.main())