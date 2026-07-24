#!/usr/bin/env python3
"""Valida chamadas literais do frontend contra o schema OpenAPI do backend.

O validador é deliberadamente conservador: apenas chamadas cujo primeiro argumento é
uma string literal ou template string são tratadas como contrato verificável. URLs
montadas inteiramente em runtime são registradas como dinâmicas no relatório, sem
serem consideradas válidas por inferência.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SOURCE_SUFFIXES = {".ts", ".tsx"}
EXCLUDED_PARTS = {"e2e", "node_modules", ".next", "__tests__"}
REQUIRED_PREFIXES = (
    "/api/v1/auth/",
    "/api/v1/organizations/",
    "/api/v1/patients/",
    "/api/v1/records/",
    "/api/v1/scheduling/",
    "/api/v1/finances/",
    "/api/v1/documents/",
    "/api/v1/reports/",
    "/api/v1/forms/",
    "/api/v1/billing/",
    "/api/v1/communications/",
)


@dataclass(frozen=True)
class FrontendCall:
    method: str
    path: str
    source: str
    line: int


@dataclass(frozen=True)
class MissingOperation:
    method: str
    path: str
    source: str
    line: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--frontend-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args()


def _skip_balanced_generic(text: str, index: int) -> int:
    if index >= len(text) or text[index] != "<":
        return index
    depth = 0
    quote = ""
    escaped = False
    while index < len(text):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
        else:
            if char in {"'", '"', "`"}:
                quote = char
            elif char == "<":
                depth += 1
            elif char == ">":
                depth -= 1
                if depth == 0:
                    return index + 1
        index += 1
    return index


def _read_quoted_literal(text: str, index: int) -> tuple[str | None, int]:
    if index >= len(text) or text[index] not in {"'", '"', "`"}:
        return None, index
    quote = text[index]
    index += 1
    output: list[str] = []
    escaped = False
    while index < len(text):
        char = text[index]
        if escaped:
            output.append(char)
            escaped = False
        elif char == "\\":
            output.append(char)
            escaped = True
        elif char == quote:
            return "".join(output), index + 1
        else:
            output.append(char)
        index += 1
    return None, index


def extract_frontend_calls(frontend_root: Path) -> tuple[list[FrontendCall], int]:
    calls: list[FrontendCall] = []
    dynamic_calls = 0
    pattern = re.compile(r"\bapi\.(get|post|put|patch|delete)\b")

    for source_path in sorted(frontend_root.rglob("*")):
        if source_path.suffix not in SOURCE_SUFFIXES:
            continue
        if any(part in EXCLUDED_PARTS for part in source_path.parts):
            continue
        if ".test." in source_path.name or ".spec." in source_path.name:
            continue
        text = source_path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            method = match.group(1).lower()
            index = match.end()
            while index < len(text) and text[index].isspace():
                index += 1
            index = _skip_balanced_generic(text, index)
            while index < len(text) and text[index].isspace():
                index += 1
            if index >= len(text) or text[index] != "(":
                dynamic_calls += 1
                continue
            index += 1
            while index < len(text) and text[index].isspace():
                index += 1
            literal, _ = _read_quoted_literal(text, index)
            if literal is None:
                dynamic_calls += 1
                continue
            normalized = normalize_frontend_path(literal)
            if normalized is None:
                dynamic_calls += 1
                continue
            calls.append(
                FrontendCall(
                    method=method,
                    path=normalized,
                    source=str(source_path.relative_to(frontend_root.parent.parent)),
                    line=text.count("\n", 0, match.start()) + 1,
                )
            )
    return calls, dynamic_calls


def normalize_frontend_path(raw_path: str) -> str | None:
    path = raw_path.strip()
    if not path or path.startswith(("http://", "https://")):
        return None
    path = path.split("?", 1)[0].split("#", 1)[0]
    path = re.sub(r"\$\{[^}]+\}", "{dynamic}", path)
    path = path.removeprefix("/api/backend/")
    path = path.removeprefix("api/backend/")
    if path.startswith("/api/v1/"):
        normalized = path
    elif path.startswith("api/v1/"):
        normalized = f"/{path}"
    else:
        normalized = f"/api/v1/{path.lstrip('/')}"
    return normalize_path(normalized)


def normalize_path(path: str) -> str:
    clean = re.sub(r"/{2,}", "/", path.strip())
    if not clean.startswith("/"):
        clean = f"/{clean}"
    if not clean.endswith("/"):
        clean = f"{clean}/"
    return clean


def _path_matches(schema_path: str, frontend_path: str) -> bool:
    schema_segments = normalize_path(schema_path).strip("/").split("/")
    frontend_segments = normalize_path(frontend_path).strip("/").split("/")
    if len(schema_segments) != len(frontend_segments):
        return False
    for schema_segment, frontend_segment in zip(schema_segments, frontend_segments, strict=True):
        schema_dynamic = schema_segment.startswith("{") and schema_segment.endswith("}")
        frontend_dynamic = frontend_segment.startswith("{") and frontend_segment.endswith("}")
        if schema_dynamic or frontend_dynamic:
            continue
        if schema_segment != frontend_segment:
            return False
    return True


def load_schema(schema_path: Path) -> dict[str, Any]:
    payload = json.loads(schema_path.read_text(encoding="utf-8"))
    if not str(payload.get("openapi", "")).startswith("3."):
        raise ValueError("O arquivo não contém um schema OpenAPI 3.x válido.")
    paths = payload.get("paths")
    if not isinstance(paths, dict) or not paths:
        raise ValueError("O schema OpenAPI não contém operações em paths.")
    return payload


def validate_contract(schema: dict[str, Any], calls: list[FrontendCall]) -> tuple[list[str], list[MissingOperation]]:
    schema_paths: dict[str, Any] = {
        normalize_path(str(path)): operations
        for path, operations in schema["paths"].items()
        if isinstance(operations, dict)
    }
    missing_prefixes = [
        prefix
        for prefix in REQUIRED_PREFIXES
        if not any(path.startswith(prefix) for path in schema_paths)
    ]
    missing_operations: list[MissingOperation] = []
    for call in calls:
        matched = False
        for schema_path, operations in schema_paths.items():
            if not _path_matches(schema_path, call.path):
                continue
            if call.method in operations:
                matched = True
                break
        if not matched:
            missing_operations.append(
                MissingOperation(
                    method=call.method.upper(),
                    path=call.path,
                    source=call.source,
                    line=call.line,
                )
            )
    return missing_prefixes, missing_operations


def main() -> int:
    args = parse_args()
    try:
        schema = load_schema(args.schema)
        calls, dynamic_calls = extract_frontend_calls(args.frontend_root)
        missing_prefixes, missing_operations = validate_contract(schema, calls)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Falha ao validar contrato: {exc}", file=sys.stderr)
        return 2

    report = {
        "schema": str(args.schema),
        "frontend_root": str(args.frontend_root),
        "schema_paths": len(schema["paths"]),
        "literal_calls_checked": len(calls),
        "dynamic_calls_skipped": dynamic_calls,
        "missing_prefixes": missing_prefixes,
        "missing_operations": [asdict(item) for item in missing_operations],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if missing_prefixes or missing_operations:
        for prefix in missing_prefixes:
            print(f"Prefixo obrigatório ausente no OpenAPI: {prefix}", file=sys.stderr)
        for item in missing_operations:
            print(
                f"Contrato ausente: {item.method} {item.path} ({item.source}:{item.line})",
                file=sys.stderr,
            )
        return 1

    print(
        "Contrato validado: "
        f"{len(calls)} chamada(s) literal(is), {dynamic_calls} dinâmica(s), "
        f"{len(schema['paths'])} caminho(s) OpenAPI."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
